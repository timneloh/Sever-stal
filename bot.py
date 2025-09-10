import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from db import init_db
from handlers import router

async def main():
    print("LOG: Инициализация...")
    init_db()
    
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("LOG: Bot создан")
    
    dp = Dispatcher()
    dp.include_router(router)
    print("LOG: Роутер подключен")
    
    print("LOG: Запуск polling...")
    await bot.delete_webhook(drop_pending_updates=True) # Пропускаем старые апдейты
    await dp.start_polling(bot)
    print("LOG: Polling завершился")

if __name__ == '__main__':
    print("LOG: Старт main()")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("LOG: Бот остановлен вручную")
    print("LOG: Выход из программы")
