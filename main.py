import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import load_config
from database import init_db


async def main():
    from botHandlers import dp
    logging.basicConfig(level=logging.INFO)

    # Загрузка конфигурации
    config = load_config()
    bot = Bot(token=config["token"])

    # Инициализация базы данных
    init_db()

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
