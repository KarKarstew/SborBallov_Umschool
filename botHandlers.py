import re
from database import session, Student, Score
from config import load_config
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards import *

# Обработчик для бота
dp = Dispatcher()

# Предметы экзамена
config = load_config()
ege_subjects = config["ЕГЭ"]
oge_subjects = config["ОГЭ"]

# Регулярное выражение для проверки почты
email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


# Определение состояний для регистрации
class RegistrationState(StatesGroup):
    awaiting_name = State()
    awaiting_email = State()
    awaiting_exam_type = State()
    confirming_exam_type = State()

# Определение состояний для ввода баллов
class ScoreInput(StatesGroup):
    choosing_subject = State()
    entering_score = State()
    waiting_for_confirmation = State()
    final_confirmation = State()


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Добро пожаловать в бота для учета баллов ЕГЭ/ОГЭ.\nИспользуйте команду /register для регистрации",
        reply_markup=register_keyboard
    )

# Регистрация пользователя
@dp.message(Command("register"))
async def register_command(message: types.Message, state: FSMContext):
    existing_student = session.query(Student).filter_by(tg_id=message.from_user.id).first()

    if existing_student:
        await message.answer("Вы уже зарегистрированы! Используйте /enter_scores для ввода баллов")
        return

    await message.answer(
        "Введите ваше имя и фамилию (пример: Иван Иванов)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationState.awaiting_name)


# Получение ФИ
@dp.message(RegistrationState.awaiting_name)
async def get_name(message: types.Message, state: FSMContext):
    name_parts = message.text.split()
    if len(name_parts) != 2:
        await message.answer("Введите имя и фамилию в правильном формате (пример: Иван Иванов)")
        return

    await state.update_data(
        first_name=name_parts[0],
        last_name=name_parts[1]
    )
    await message.answer("Введите вашу почту с платформы Умскул (пример: example@example.com)")
    await state.set_state(RegistrationState.awaiting_email)


# Получение почты
@dp.message(RegistrationState.awaiting_email)
async def get_email(message: types.Message, state: FSMContext):
    email = message.text.strip()

    # Проверка на корректность почты
    if not re.match(email_regex, email):
        await message.answer("Введите корректный адрес электронной почты")
        return

    # Проверка на наличие такой почты в БД
    bd_student = session.query(Student).filter_by(email=email).first()
    if bd_student:
        await message.answer("Пользователь с такой почтой уже внес свои баллы!")
        return

    await state.update_data(email=email)
    await message.answer(
        "Выберите тип экзамена",
        reply_markup=exam_keyboard
    )
    await state.set_state(RegistrationState.awaiting_exam_type)


# Тип экзамена
@dp.message(RegistrationState.awaiting_exam_type)
async def get_exam_type(message: types.Message, state: FSMContext):
    if message.text not in ["ЕГЭ", "ОГЭ"]:
        await message.answer("Выберите корректный экзамен (ЕГЭ или ОГЭ)")
        return

    await state.update_data(exam_type=message.text)
    await message.answer(
        f"Вы выбрали {message.text}. Подтвердите выбор или измените его",
        reply_markup=confirm_exam_keyboard
    )
    await state.set_state(RegistrationState.confirming_exam_type)


# Подтверждение выбора экзамена
@dp.message(RegistrationState.confirming_exam_type)
async def confirm_exam_type(message: types.Message, state: FSMContext):
    if message.text == "Изменить выбор":
        await message.answer(
            "Выберите тип экзамена",
            reply_markup=exam_keyboard
        )
        await state.set_state(RegistrationState.awaiting_exam_type)
    elif message.text == "Подтвердить":
        data = await state.get_data()
        new_student = Student(
            tg_id=message.from_user.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            exam_type=data["exam_type"]
        )
        session.add(new_student)
        session.commit()

        await message.answer(
            "Регистрация завершена! Используйте /enter_scores для ввода баллов",
            reply_markup=enter_scores_keyboard
        )
        await state.clear()
    else:
        await message.answer("Выберите 'Подтвердить' или 'Изменить выбор'")


# Начать выбор предметов
@dp.message(Command("enter_scores"))
async def enter_scores_command(message: types.Message, state: FSMContext):
    student = session.query(Student).filter_by(tg_id=message.from_user.id).first()
    if not student:
        await message.answer("Вы не зарегистрированы! Используйте /register")
        return

    buttons = []
    subjects = ege_subjects if student.exam_type == "ЕГЭ" else oge_subjects
    for subject in subjects:
        button = KeyboardButton(text=subject)
        buttons.append([button])
    subjects_keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer(
        "Выберите предмет, по которому хотите ввести баллы:",
        reply_markup=subjects_keyboard
    )
    await state.set_state(ScoreInput.choosing_subject)


# Выбор предмета
@dp.message(ScoreInput.choosing_subject)
async def get_subject(message: types.Message, state: FSMContext):
    student = session.query(Student).filter_by(tg_id=message.from_user.id).first()

    subjects = ege_subjects if student.exam_type == "ЕГЭ" else oge_subjects
    if message.text not in subjects:
        await message.answer("Выберите корректный предмет.")
        return

    await state.update_data(selected_subject=message.text)
    await message.answer(
        f"Введите ваш балл по {message.text} (0-100):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ScoreInput.entering_score)


# Ввод балла
@dp.message(ScoreInput.entering_score)
async def get_score(message: types.Message, state: FSMContext):
    try:
        score = int(message.text)
        if score < 0 or score > 100:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректный балл от 0 до 100")
        return

    data = await state.get_data()
    selected_subject = data["selected_subject"]
    student = session.query(Student).filter_by(tg_id=message.from_user.id).first()

    # Существует ли уже запись с этим предметом
    db_score = session.query(Score).filter_by(student_id=student.student_id, subject=selected_subject).first()

    if db_score:
        db_score.score = score
        session.commit()
        await message.answer(
            f"Балл по {selected_subject} обновлен на {score}!",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        new_score = Score(
            student_id=student.student_id,
            subject=selected_subject,
            score=score
        )
        session.add(new_score)
        session.commit()
        await message.answer(
            f"Балл по {selected_subject} сохранен!",
            reply_markup=ReplyKeyboardRemove()
        )

    await message.answer(
        "Хотите ввести ещё один предмет?",
        reply_markup=yes_no_keyboard
    )
    await state.set_state(ScoreInput.waiting_for_confirmation)


# Подтверждение
@dp.message(ScoreInput.waiting_for_confirmation)
async def confirm_input(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        student = session.query(Student).filter_by(tg_id=message.from_user.id).first()

        buttons = []
        subjects = ege_subjects if student.exam_type == "ЕГЭ" else oge_subjects
        for subject in subjects:
            button = KeyboardButton(text=subject)
            buttons.append([button])
        subjects_keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

        await message.answer(
            "Выберите предмет для ввода балла:",
            reply_markup=subjects_keyboard
        )
        await state.set_state(ScoreInput.choosing_subject)

    elif message.text.lower() == "нет":
        await message.answer(
            "Проверьте введенные баллы",
            reply_markup=ReplyKeyboardRemove()
        )

        student = session.query(Student).filter_by(tg_id=message.from_user.id).first()
        scores = session.query(Score).filter_by(student_id=student.student_id).all()

        if scores:
            score_all = "\n".join([f"{score.subject}: {score.score}" for score in scores])
            await message.answer(f"Ваши баллы:\n{score_all}")
        else:
            await message.answer("Вы ещё не ввели баллы.")

        await message.answer(
            "Хотите завершить?",
            reply_markup=yes_no_keyboard
        )
        await state.set_state(ScoreInput.final_confirmation)


# Завершение
@dp.message(ScoreInput.final_confirmation)
async def final_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        await message.answer(
            "Спасибо за использование бота!",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await message.answer("Теперь вы можете использовать команду /view_scores, чтобы просмотреть ваши баллы.")
    elif message.text.lower() == "нет":
        student = session.query(Student).filter_by(tg_id=message.from_user.id).first()

        buttons = []
        subjects = ege_subjects if student.exam_type == "ЕГЭ" else oge_subjects
        for subject in subjects:
            button = KeyboardButton(text=subject)
            buttons.append([button])
        subjects_keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

        await message.answer(
            "Вы можете ввести еще баллы",
            reply_markup=subjects_keyboard
        )
        await state.set_state(ScoreInput.choosing_subject)


# Просмотр баллов
@dp.message(Command("view_scores"))
async def view_scores_command(message: types.Message):
    student = session.query(Student).filter_by(tg_id=message.from_user.id).first()
    if not student:
        await message.answer("Вы не зарегистрированы! Используйте /register.")
        return

    scores = session.query(Score).filter_by(student_id=student.student_id).all()

    if scores:
        score_all = "\n".join([f"{score.subject}: {score.score}" for score in scores])
        await message.answer(f"Ваши баллы:\n{score_all}")
    else:
        await message.answer("Вы ещё не ввели баллы.")
