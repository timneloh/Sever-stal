import sqlite3
import json

DB_FILE = "db.sqlite"  # Путь к базе данных

def init_db():
    print("LOG: Инициализация базы данных...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Создаем основную таблицу
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            rewards TEXT DEFAULT '[]'
        )
    ''')

    # Список колонок, которые должны быть в таблице
    required_columns = {
        "day1_completed": "INTEGER DEFAULT 0",
        "day2_cards_opened": "TEXT DEFAULT '[]'",
        "day2_completed": "INTEGER DEFAULT 0"
    }

    # Получаем информацию о текущих колонках
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Добавляем недостающие колонки
    for col, col_type in required_columns.items():
        if col not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
                print(f"LOG: Колонка '{col}' успешно добавлена.")
            except sqlite3.OperationalError as e:
                print(f"LOG ERROR: Не удалось добавить колонку {col}: {e}")

    conn.commit()
    conn.close()
    print("LOG: Инициализация БД завершена.")

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

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

def mark_day1_completed(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET day1_completed = 1 WHERE id = ?', (user_id,))
    conn.commit()
    print(f"LOG WRITE: Для пользователя ID={user_id} день 1 отмечен как пройденный.")
    conn.close()

def has_completed_day1(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT day1_completed FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def add_reward(user_id, reward):
    # (Функция без изменений)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT rewards FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    rewards = json.loads(row[0])
    if reward not in rewards:
        rewards.append(reward)
    cursor.execute('UPDATE users SET rewards = ? WHERE id = ?', (json.dumps(rewards), user_id))
    conn.commit()
    print(f"LOG WRITE: Пользователю ID={user_id} добавлена награда '{reward}'.")
    conn.close()

def get_profile(user_id):
    # (Функция без изменений)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, points, rewards FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    rewards = json.loads(user[3]) if user[3] else []
    return {
        "id": user[0],
        "username": user[1],
        "points": user[2],
        "rewards": rewards
    }

# --- Новые функции для Дня 2 ---

def get_day2_progress(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT day2_cards_opened, day2_completed FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"opened_cards": [], "completed": False}
    
    opened_cards = json.loads(row[0])
    return {"opened_cards": opened_cards, "completed": bool(row[1])}

def mark_day2_card_opened(user_id, card_idx):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Получаем текущий список
    cursor.execute('SELECT day2_cards_opened FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
        
    opened_cards = json.loads(row[0])
    if card_idx not in opened_cards:
        opened_cards.append(card_idx)
    
    # Обновляем список и проверяем, не завершен ли день
    cursor.execute('UPDATE users SET day2_cards_opened = ? WHERE id = ?', (json.dumps(opened_cards), user_id))
    
    # Если открыты все 5 карточек, помечаем день как пройденный
    if len(opened_cards) >= 5:
        cursor.execute('UPDATE users SET day2_completed = 1 WHERE id = ?', (user_id,))
        print(f"LOG WRITE: Для пользователя ID={user_id} день 2 отмечен как пройденный.")

    conn.commit()
    print(f"LOG WRITE: Пользователь ID={user_id} открыл карточку Дня 2 #{card_idx}.")
    conn.close()
