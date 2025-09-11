import os

# --- Секретные данные ---
# Загружаются из .env файла при старте бота в bot.py
TOKEN = os.getenv("TOKEN")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# --- Общие настройки ---

# Количество дней мероприятия или теста
EVENT_DAYS = 5

# Ссылка на подкаст или любой внешний ресурс
PODCAST_URL = "https://example.com"

# Список Telegram ID администраторов бота (укажите свои ID)
ADMINS = {5936396425, 1995633871} # Пример
