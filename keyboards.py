from aiogram import types
from config import PODCAST_URL

def main_menu_kb() -> types.ReplyKeyboardMarkup:
    buttons = [
        [types.KeyboardButton(text="Начать день")],
        [types.KeyboardButton(text="Профиль"), types.KeyboardButton(text="Помощь")],
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def day1_mode_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Ты на работе (серьёзный тест)", callback_data="day1:serious")],
        [types.InlineKeyboardButton(text="Твоё Альтер-эго (шуточный тест)", callback_data="day1:fun")],
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")],
    ])

def back_to_menu_inline() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")]
    ])

def slider_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="1", callback_data="slider:1"),
            types.InlineKeyboardButton(text="2", callback_data="slider:2"),
            types.InlineKeyboardButton(text="3", callback_data="slider:3"),
            types.InlineKeyboardButton(text="4", callback_data="slider:4"),
            types.InlineKeyboardButton(text="5", callback_data="slider:5")
        ]
    ])

def mc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [
        [types.InlineKeyboardButton(text=opt[0], callback_data=f"mc:{i}")]
        for i, opt in enumerate(q["options"])
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def assoc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [
        [types.InlineKeyboardButton(text=icon, callback_data=f"assoc:{i}")]
        for i, icon in enumerate(q["icons"])
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def fun_test_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [
        [types.InlineKeyboardButton(text=opt[0], callback_data=f"fun:{i}")]
        for i, opt in enumerate(q["options"])
    ]
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

def day2_cards_kb(opened_cards: list[int]) -> types.InlineKeyboardMarkup:
    buttons = []
    for i in range(5):
        if i in opened_cards:
            text = f"✅ Карточка {i+1} (открыто)"
            cb_data = f"day2:opened"
        else:
            text = f"🎴 Карточка {i+1}"
            cb_data = f"day2:card:{i}"
        buttons.append([types.InlineKeyboardButton(text=text, callback_data=cb_data)])
    
    buttons.append([types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

