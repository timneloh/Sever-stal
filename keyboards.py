from aiogram import types
from config import EVENT_DAYS
import texts

def main_menu_kb() -> types.ReplyKeyboardMarkup:
    buttons = [
        [types.KeyboardButton(text="Выбрать день")],
        [types.KeyboardButton(text="Генератор мемов")],
        [types.KeyboardButton(text="Профиль"), types.KeyboardButton(text="Помощь")],
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def days_menu_kb(open_days: list[int]) -> types.InlineKeyboardMarkup:
    buttons = []
    for i in range(1, EVENT_DAYS + 1):
        if i in open_days:
            text = f"День {i}"
            callback_data = f"select_day:{i}"
        else:
            text = f"🔒 День {i} (Закрыто)"
            callback_data = "day_locked"
        buttons.append([types.InlineKeyboardButton(text=text, callback_data=callback_data)])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_menu_inline() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="В главное меню", callback_data="nav:main")]
    ])

def profile_kb(show_rewards: bool = False) -> types.InlineKeyboardMarkup:
    buttons = []
    if show_rewards:
        buttons.append([types.InlineKeyboardButton(text="Получить сертификат", callback_data="get_certificate")])
        buttons.append([types.InlineKeyboardButton(text="Получить стикеры", url="https://t.me/addstickers/NedelyaZnanij2025")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# --- День 1 ---
def day1_mode_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Ты на работе (серьёзный тест)", callback_data="day1:serious")],
        [types.InlineKeyboardButton(text="Твоё Альтер-эго (шуточный тест)", callback_data="day1:fun")],
    ])

def slider_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=str(i), callback_data=f"slider:{i}") for i in range(1, 6)]
    ])

def mc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"mc:{i}")] for i, opt in enumerate(q["options"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def assoc_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"assoc:{i}")] for i, icon in enumerate(q["icons"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def fun_test_kb(q: dict) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"fun:{i}")] for i, opt in enumerate(q["options"])]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def disc_result_kb(share_text: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔗 Поделиться", switch_inline_query=share_text)],
        [types.InlineKeyboardButton(text="🔄 Пройти другой тест", callback_data="day1:choose_again")],
        [types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 1 дня (5 мин.)", callback_data="podcast:1")],
    ])

def fun_result_kb(share_text: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔗 Поделиться", switch_inline_query=share_text)],
        [types.InlineKeyboardButton(text="🔄 Пройти другой тест", callback_data="day1:choose_again")],
        [types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 1 дня (5 мин.)", callback_data="podcast:1")],
    ])

# --- День 2 ---
def day2_cards_kb(opened_cards: list[int]) -> types.InlineKeyboardMarkup:
    buttons = []
    for i in range(5):
        text = f"✅ Карточка {i+1} (открыто)" if i in opened_cards else f"🎴 Карточка {i+1}"
        cb_data = "day2:opened" if i in opened_cards else f"day2:card:{i}"
        buttons.append([types.InlineKeyboardButton(text=text, callback_data=cb_data)])
    buttons.append([types.InlineKeyboardButton(text="Пройти опрос на эмпатию (30 мин.)", callback_data="day2:empathy_test")])
    buttons.append([types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 2 дня (5 мин.)", callback_data="podcast:2")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day2_after_card_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Назад к карточкам", callback_data="day2:back_to_cards")]
    ])

def empathy_test_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="Пройти тест",
            url="https://lk.severstal.com/needauth?url=https://study-srv.severstal.com/fiori#zhcmi713_ui5-display&/event?trainingId=90133771%26trainingType=D"
        )]
    ])

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
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day3_comics_choice_kb(choices: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"day3:comics_choice:{i}")] for i, choice in enumerate(choices)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day3_after_comics_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Пройти викторину", callback_data="day3:start_quiz")],
        [types.InlineKeyboardButton(text="Выбрать другого героя", callback_data="day3:choose_another_hero")],
        [types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 3 дня (5 мин.)", callback_data="podcast:3")],
    ])

def day3_quiz_kb(options: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"day3:quiz_answer:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day3_quiz_next_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Далее ➡️", callback_data="day3:quiz_next")]
    ])


# --- День 4 ---
def day4_quiz_kb(options: list, case_idx: int) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"day4:answer:{case_idx}:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def day4_after_quiz_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 4 дня (5 мин.)", callback_data="podcast:4")]
    ])

# --- День 5 ---
def day5_quiz_kb(options: list) -> types.InlineKeyboardMarkup:
    buttons = [[types.InlineKeyboardButton(text=str(i+1), callback_data=f"day5:answer:{i}")] for i, option in enumerate(options)]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)
    
def day5_after_quiz_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Пройти рефлексию", callback_data="day5:start_reflection")],
        [types.InlineKeyboardButton(text=f"🎧 {texts.PODCAST_TITLE} 5 дня (5 мин.)", callback_data="podcast:5")]
    ])

def day5_next_question_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Следующий вопрос", callback_data="day5:next_question")]
    ])

def day5_finish_quiz_kb() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Завершить квиз", callback_data="day5:finish_quiz")]
    ])