import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv() # Загружаем переменные из .env файла

from config import TOKEN, EVENT_DAYS
from db import init_db, get_current_day, set_current_day
from handlers import router as main_router
from day1_handler import router as day1_router
from day2_handler import router as day2_router
from day3_handler import router as day3_router
from day4_handler import router as day4_router
from day5_handler import router as day5_router

# Функция для автоматической смены дня
async def advance_day():
    current_day = await get_current_day()
    if current_day is None:
        current_day = 1
    else:
        current_day += 1
    
    if current_day <= EVENT_DAYS:
        await set_current_day(current_day)
        print(f"LOG: Автоматическая смена дня. Новый день: {current_day}")
    else:
        print("LOG: Марафон завершен. Смена дня остановлена.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("LOG: Инициализация...")
    await init_db()
    
    # Установка начального дня, если он не задан
    if await get_current_day() is None:
        await set_current_day(1)
        print("LOG: Установлен начальный день: 1")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("LOG: Bot создан")
    
    dp = Dispatcher()
    dp.include_router(main_router)
    dp.include_router(day1_router)
    dp.include_router(day2_router)
    dp.include_router(day3_router)
    dp.include_router(day4_router)
    dp.include_router(day5_router)
    print("LOG: Роутеры подключены")
    
    # Настройка планировщика для смены дня каждый день в 00:00
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(advance_day, 'cron', hour=0, minute=0)
    scheduler.start()
    print("LOG: Планировщик для смены дня запущен.")

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

