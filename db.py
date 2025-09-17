import asyncpg
import json
from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME, EVENT_DAYS

POOL = None

async def get_pool():
    """Создает и возвращает пул соединений к базе данных."""
    global POOL
    if POOL is None:
        print("LOG: Создание пула соединений с PostgreSQL...")
        try:
            POOL = await asyncpg.create_pool(
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                host=DB_HOST,
                port=DB_PORT
            )
            print("LOG: Пул соединений успешно создан.")
        except Exception as e:
            print(f"FATAL: Не удалось подключиться к PostgreSQL: {e}")
            # В реальном приложении здесь может быть более сложная логика
            # Например, попытки переподключения или аварийное завершение
            raise
    return POOL

async def init_db():
    """Инициализирует таблицы в базе данных."""
    print("LOG: Инициализация базы данных PostgreSQL...")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0,
                rewards JSONB DEFAULT '[]'::jsonb,
                results JSONB DEFAULT '[]'::jsonb,
                reflection TEXT
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS daily_progress (
                user_id BIGINT,
                day_number INTEGER,
                completed INTEGER DEFAULT 0,
                data JSONB DEFAULT '{}'::jsonb,
                PRIMARY KEY (user_id, day_number),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
    print("LOG: Инициализация БД PostgreSQL завершена.")

# --- Состояние бота ---
async def set_bot_state(key, value):
    pool = await get_pool()
    await pool.execute('INSERT INTO bot_state (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2', key, str(value))

async def get_bot_state(key):
    pool = await get_pool()
    value = await pool.fetchval('SELECT value FROM bot_state WHERE key = $1', key)
    return value

async def get_current_day():
    day = await get_bot_state('current_day')
    return int(day) if day else None

async def set_current_day(day: int):
    await set_bot_state('current_day', day)
    print(f"LOG WRITE: Текущий день изменен на {day}")

# --- Пользователи ---
async def create_user(user_id, username):
    pool = await get_pool()
    # ON CONFLICT DO NOTHING игнорирует вставку, если пользователь уже существует
    result = await pool.execute('INSERT INTO users (id, username) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING', user_id, username)
    if result == 'INSERT 0 1':
        print(f"LOG WRITE: Создан пользователь с ID={user_id}, username='{username}'")

async def update_points(user_id, points_to_add):
    pool = await get_pool()
    await pool.execute('UPDATE users SET points = points + $1 WHERE id = $2', points_to_add, user_id)
    print(f"LOG WRITE: Пользователю ID={user_id} добавлено {points_to_add} очков.")

async def get_profile(user_id):
    pool = await get_pool()
    # fetchrow возвращает asyncpg.Record, который работает как словарь
    user_row = await pool.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
    return dict(user_row) if user_row else None

async def add_result(user_id, result_text):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            results_val = await conn.fetchval('SELECT results FROM users WHERE id = $1', user_id)
            
            if results_val is None:
                results = []
            elif isinstance(results_val, str):
                results = json.loads(results_val)
            else:
                results = results_val

            if result_text not in results:
                results.append(result_text)
                await conn.execute('UPDATE users SET results = $1 WHERE id = $2', json.dumps(results), user_id)
                print(f"LOG WRITE: Пользователю ID={user_id} добавлен результат '{result_text}'.")

# --- Прогресс по дням ---
async def mark_day_completed(user_id, day_number):
    pool = await get_pool()
    await pool.execute(
        'INSERT INTO daily_progress (user_id, day_number, completed) VALUES ($1, $2, 1) '
        'ON CONFLICT (user_id, day_number) DO UPDATE SET completed = 1',
        user_id, day_number
    )
    print(f"LOG WRITE: Для пользователя ID={user_id} день {day_number} отмечен как пройденный.")

async def has_completed_day(user_id, day_number):
    pool = await get_pool()
    result = await pool.fetchval('SELECT completed FROM daily_progress WHERE user_id = $1 AND day_number = $2', user_id, day_number)
    return result == 1

async def get_day_progress(user_id, day_number):
    pool = await get_pool()
    data = await pool.fetchval('SELECT data FROM daily_progress WHERE user_id = $1 AND day_number = $2', user_id, day_number)
    return data if data else {}

async def update_day_progress_data(user_id, day_number, new_data_dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            current_data_str = await conn.fetchval('SELECT data FROM daily_progress WHERE user_id = $1 AND day_number = $2', user_id, day_number)
            
            if isinstance(current_data_str, str):
                current_data = json.loads(current_data_str)
            else:
                current_data = current_data_str if current_data_str else {}

            current_data.update(new_data_dict)
            
            await conn.execute(
                'INSERT INTO daily_progress (user_id, day_number, data) VALUES ($1, $2, $3) '
                'ON CONFLICT (user_id, day_number) DO UPDATE SET data = $3',
                user_id, day_number, json.dumps(current_data)
            )

async def mark_card_opened(user_id, day_number, card_idx):
    progress_str = await get_day_progress(user_id, day_number)
    progress = json.loads(progress_str) if isinstance(progress_str, str) else progress_str
    opened_cards = progress.get("cards_opened", [])
    if card_idx not in opened_cards:
        opened_cards.append(card_idx)
    await update_day_progress_data(user_id, day_number, {"cards_opened": opened_cards})
    print(f"LOG WRITE: Пользователь ID={user_id} открыл карточку Дня {day_number} #{card_idx}.")

async def has_completed_all_days(user_id):
    pool = await get_pool()
    completed_days = await pool.fetchval('SELECT COUNT(*) FROM daily_progress WHERE user_id = $1 AND completed = 1', user_id)
    return (completed_days or 0) >= EVENT_DAYS

async def reset_user_progress(user_id):
    """Сбрасывает прогресс пользователя."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Сброс очков и связанных данных в таблице users
            await conn.execute(
                "UPDATE users SET points = 0, rewards = '[]'::jsonb, results = '[]'::jsonb, reflection = NULL WHERE id = $1",
                user_id
            )
            # Удаление всего прогресса по дням
            await conn.execute('DELETE FROM daily_progress WHERE user_id = $1', user_id)
    print(f"LOG WRITE: Прогресс для пользователя ID={user_id} был полностью сброшен.")