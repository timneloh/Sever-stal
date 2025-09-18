import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv() # Загружаем переменные из .env файла

from config import TOKEN
from db import init_db, init_days
from handlers import router as main_router
from day1_handler import router as day1_router
from day2_handler import router as day2_router
from day3_handler import router as day3_router
from day4_handler import router as day4_router
from day5_handler import router as day5_router

async def main():
    logging.basicConfig(level=logging.INFO)
    print("LOG: Инициализация...")
    await init_db()
    await init_days() # Инициализируем дни

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("LOG: Bot создан")
    
    dp = Dispatcher()
    dp.include_router(day1_router)
    dp.include_router(day2_router)
    dp.include_router(day3_router)
    dp.include_router(day4_router)
    dp.include_router(day5_router)
    dp.include_router(main_router) # Этот роутер должен быть последним
    print("LOG: Роутеры подключены")

    print("LOG: Запуск polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    print("LOG: Polling завершился")

if __name__ == '__main__':
    print("LOG: Старт main()")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("LOG: Бот остановлен вручную")
    print("LOG: Выход из программы")

