import logging
import uuid
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from config import EVENT_DAYS
import db
import keyboards
from commands import USER_COMMANDS_TEXT, ADMIN_COMMANDS_TEXT
from utils import is_admin, to_main_menu # <-- ИМПОРТ ИЗ UTILS

# Импортируем стартовые функции для каждого дня
from day1_handler import start_day1
from day2_handler import start_day2
from day3_handler import start_day3
from day4_handler import start_day4
from day5_handler import start_day5

router = Router()

# ===== Вспомогательные функции =====



# ===== Основные команды =====

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    db.create_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await message.answer_photo(
        photo=types.FSInputFile("img/Старт.png"), 
        caption="Привет! Это бот «Неделя знаний Северсталь». Нажмите «Начать день», чтобы перейти к активностям.",
        reply_markup=keyboards.main_menu_kb()
    )

@router.message(F.text.in_({"Помощь", "/help"}))
async def btn_help(message: types.Message):
    await message.answer(USER_COMMANDS_TEXT, parse_mode=None)

@router.message(F.text == "Профиль")
async def btn_profile(message: types.Message):
    profile = db.get_profile(message.from_user.id)
    if not profile:
        await message.answer("Профиль не найден. Нажмите /start, чтобы начать.", reply_markup=keyboards.main_menu_kb())
        return

    # Логика наград
    rewards = profile.get('rewards', [])
    if db.has_completed_all_days(message.from_user.id):
        if "Мастер коммуникаций" not in rewards:
            rewards.append("Мастер коммуникаций")
    
    rewards_text = ', '.join(rewards) if rewards else "0"
    results_text = ', '.join(profile.get('results', [])) if profile.get('results') else "0"

    caption = (
        f"<b>Профиль:</b>\n"
        f"ID: <code>{profile['id']}</code>\n"
        f"Логин: {profile['username'] or '—'}\n"
        f"Баллы: {profile['points']}\n\n"
        f"<b>Результаты:</b> {results_text}\n"
        f"<b>Награды:</b> {rewards_text}"
    )

    await message.answer_photo(
        photo=types.FSInputFile("img/13.png"),
        caption=caption
    )
    
    # Выдача Digital Badge и сертификата
    if "Мастер коммуникаций" in rewards:
        await message.answer_document(
            document=types.FSInputFile("files/Digital_Badge.png"),
            caption="Поздравляем! Вы получаете Digital Badge."
        )
        await message.answer_document(
            document=types.FSInputFile("files/Certificate.pdf"),
            caption="А также именной сертификат!"
        )

# ===== Обработка дней =====

@router.message(F.text == "Начать день")
async def btn_start_day(message: types.Message, state: FSMContext):
    db.create_user(message.from_user.id, message.from_user.username)
    current_day = db.get_current_day()

    day_starters = {
        1: start_day1,
        2: start_day2,
        3: start_day3,
        4: start_day4,
        5: start_day5,
    }
    
    starter = day_starters.get(current_day)
    if starter:
        await starter(message, state)
    else:
        await message.answer(
            f"День {current_day}: контент скоро будет доступен.",
            reply_markup=keyboards.back_to_menu_inline()
        )

@router.callback_query(F.data == "nav:main")
async def nav_main(callback: types.CallbackQuery, state: FSMContext):
    await to_main_menu(callback.message, state)
    await callback.answer()

# ===== Inline-режим для "Поделиться" =====

@router.inline_query()
async def handle_inline_share(inline_query: InlineQuery):
    query_text = inline_query.query
    if not query_text:
        return

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="Отправить результат",
        description=query_text,
        input_message_content=InputTextMessageContent(
            message_text=query_text
        ),
        thumb_url="https://w7.pngwing.com/pngs/32/933/png-transparent-steel-industry-logo-severstal-industry-company-text-trademark.png",
    )
    
    await inline_query.answer([result], cache_time=1)

# ===== Админ-команды =====

@router.message(Command("ashelp"))
async def cmd_admin_help(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer(ADMIN_COMMANDS_TEXT, parse_mode=None)

@router.message(Command("setday"))
async def cmd_set_day(message: types.Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Использование: /setday <номер_дня>")
        return
        
    day = int(args[1])
    if 1 <= day <= EVENT_DAYS:
        db.set_current_day(day)
        await message.answer(f"✅ День установлен: {day}")
    else:
        await message.answer(f"⚠️ День должен быть в диапазоне 1-{EVENT_DAYS}.")

# ===== "Ловец" всех остальных сообщений =====

@router.message()
async def unknown_message(message: types.Message):
    await message.answer("Команда не распознана. Используйте меню или /help.")

