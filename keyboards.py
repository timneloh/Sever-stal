from aiogram import types
from config import PODCAST_URL

def main_menu_kb() -> types.ReplyKeyboardMarkup:
    buttons = [
        [types.KeyboardButton(text="Начать день")],
        [types.KeyboardButton(text="Профиль"), types.KeyboardButton(text="Помощь")],
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def back_to_menu_inline() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")]
    ])

# --- День 1 ---
def day1_mode_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Ты на работе (серьёзный тест)", callback_data="day1:serious")],
        [types.InlineKeyboardButton(text="Твоё Альтер-эго (шуточный тест)", callback_data="day1:fun")],
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")],
    ])

def slider_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=str(i), callback_data=f"slider:{i}") for i in range(1, 6)]
    ])

def mc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=opt[0], callback_data=f"mc:{i}")] for i, opt in enumerate(q["options"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def assoc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=icon, callback_data=f"assoc:{i}")] for i, icon in enumerate(q["icons"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def fun_test_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=opt[0], callback_data=f"fun:{i}")] for i, opt in enumerate(q["options"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def disc_result_kb(share_text: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔗 Поделиться", switch_inline_query=share_text)],
        [types.InlineKeyboardButton(text="🔄 Пройти другой тест", callback_data="day1:choose_again")],
        [types.InlineKeyboardButton(text="🎧 Послушать подкаст (5 мин)", url=PODCAST_URL)],
    ])

def fun_result_kb(share_text: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔗 Поделиться", switch_inline_query=share_text)],
        [types.InlineKeyboardButton(text="🔄 Пройти другой тест", callback_data="day1:choose_again")],
    ])

# --- День 2 ---
def day2_cards_kb(opened_cards: list[int]) -> types.InlineKeyboardMarkup:
    buttons = []
    for i in range(5):
        text = f"✅ Карточка {i+1} (открыто)" if i in opened_cards else f"🎴 Карточка {i+1}"
        cb_data = "day2:opened" if i in opened_cards else f"day2:card:{i}"
        buttons.append([types.InlineKeyboardButton(text=text, callback_data=cb_data)])
    buttons.append([types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# --- День 3 ---
def day3_hero_select_kb(heroes_keys: list, current_idx: int) -> types.InlineKeyboardMarkup:
    total = len(heroes_keys)
    prev_idx = (current_idx - 1 + total) % total
    next_idx = (current_idx + 1) % total
    current_hero_key = heroes_keys[current_idx]

    buttons = [
        [
            types.InlineKeyboardButton(text="←", callback_data=f"day3:hero_nav:{prev_idx}"),
            types.InlineKeyboardButton(text="Выбрать", callback_data=f"day3:hero_choose:{current_hero_key}"),
            types.InlineKeyboardButton(text="→", callback_data=f"day3:hero_nav:{next_idx}")
        ],
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day3_comics_choice_kb(choices: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=choice[0], callback_data=f"day3:comics_choice:{i}")] for i, choice in enumerate(choices)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day3_after_comics_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Пройти викторину", callback_data="day3:start_quiz")],
        [types.InlineKeyboardButton(text="Выбрать другого героя", callback_data="day3:choose_another_hero")],
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")]
    ])

def day3_quiz_kb(options: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=option, callback_data=f"day3:quiz_answer:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


# --- День 4 ---
def day4_quiz_kb(options: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=option, callback_data=f"day4:answer:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# --- День 5 ---
def day5_quiz_kb(options: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=option, callback_data=f"day5:answer:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)
    
def day5_after_quiz_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Пройти рефлексию", callback_data="day5:start_reflection")]
    ])
