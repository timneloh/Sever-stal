import sqlite3
import json
from config import EVENT_DAYS

DB_FILE = "db.sqlite"

def init_db():
    print("LOG: Инициализация базы данных...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            rewards TEXT DEFAULT '[]',
            results TEXT DEFAULT '[]',
            reflection TEXT
        )
    ''')
    
    # Таблица для отслеживания прогресса по дням
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_progress (
            user_id INTEGER,
            day_number INTEGER,
            completed INTEGER DEFAULT 0,
            data TEXT DEFAULT '{}',
            PRIMARY KEY (user_id, day_number),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Таблица для хранения состояния бота
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("LOG: Инициализация БД завершена.")

# --- Состояние бота ---
def set_bot_state(key, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def get_bot_state(key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM bot_state WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_current_day():
    day = get_bot_state('current_day')
    return int(day) if day else None

def set_current_day(day: int):
    set_bot_state('current_day', day)
    print(f"LOG WRITE: Текущий день изменен на {day}")

# --- Пользователи ---
def create_user(user_id, username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"LOG WRITE: Создан пользователь с ID={user_id}, username='{username}'")
    conn.close()

def update_points(user_id, points_to_add):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE id = ?', (points_to_add, user_id))
    conn.commit()
    print(f"LOG WRITE: Пользователю ID={user_id} добавлено {points_to_add} очков.")
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    if not user_row:
        return None
    
    user_dict = dict(user_row)
    user_dict['rewards'] = json.loads(user_dict['rewards'])
    user_dict['results'] = json.loads(user_dict['results'])
    return user_dict

def add_result(user_id, result_text):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT results FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if not row: return
    
    results = json.loads(row[0])
    if result_text not in results:
        results.append(result_text)
    
    cursor.execute('UPDATE users SET results = ? WHERE id = ?', (json.dumps(results), user_id))
    conn.commit()
    print(f"LOG WRITE: Пользователю ID={user_id} добавлен результат '{result_text}'.")
    conn.close()

# --- Прогресс по дням ---
def mark_day_completed(user_id, day_number):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO daily_progress (user_id, day_number, completed, data) '
        'VALUES (?, ?, 1, COALESCE((SELECT data FROM daily_progress WHERE user_id=? AND day_number=?), \'{}\'))',
        (user_id, day_number, user_id, day_number)
    )
    conn.commit()
    print(f"LOG WRITE: Для пользователя ID={user_id} день {day_number} отмечен как пройденный.")
    conn.close()

def has_completed_day(user_id, day_number):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT completed FROM daily_progress WHERE user_id = ? AND day_number = ?', (user_id, day_number))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def get_day_progress(user_id, day_number):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM daily_progress WHERE user_id = ? AND day_number = ?', (user_id, day_number))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def update_day_progress_data(user_id, day_number, new_data_dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    current_data = get_day_progress(user_id, day_number)
    current_data.update(new_data_dict)
    
    cursor.execute(
        'INSERT OR REPLACE INTO daily_progress (user_id, day_number, completed, data) '
        'VALUES (?, ?, COALESCE((SELECT completed FROM daily_progress WHERE user_id=? AND day_number=?), 0), ?)',
        (user_id, day_number, user_id, day_number, json.dumps(current_data))
    )
    conn.commit()
    conn.close()

def mark_card_opened(user_id, day_number, card_idx):
    progress = get_day_progress(user_id, day_number)
    opened_cards = progress.get("cards_opened", [])
    if card_idx not in opened_cards:
        opened_cards.append(card_idx)
    update_day_progress_data(user_id, day_number, {"cards_opened": opened_cards})
    print(f"LOG WRITE: Пользователь ID={user_id} открыл карточку Дня {day_number} #{card_idx}.")

def has_completed_all_days(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM daily_progress WHERE user_id = ? AND completed = 1', (user_id,))
    completed_days = cursor.fetchone()[0]
    conn.close()
    return completed_days >= EVENT_DAYS
