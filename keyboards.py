from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Клавиатура для команды /register
register_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/register")]],
    resize_keyboard=True
)

# Клавиатура для выбора экзамена
exam_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="ЕГЭ")], [KeyboardButton(text="ОГЭ")]],
    resize_keyboard=True
)

# Клавиатура для Да/Нет
yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Да")], [KeyboardButton(text="Нет")]],
    resize_keyboard=True
)

# Клавиатура для подтверждения выбора экзамена
confirm_exam_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Подтвердить")], [KeyboardButton(text="Изменить выбор")]],
    resize_keyboard=True
)

# Клавиатура с кнопкой "Внести баллы"
enter_scores_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/enter_scores")]],
    resize_keyboard=True
)
