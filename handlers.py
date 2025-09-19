import logging
import uuid
import os
import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import json

from config import EVENT_DAYS
import db
import keyboards
from commands import USER_COMMANDS_TEXT, ADMIN_COMMANDS_TEXT
from utils import is_admin, to_main_menu

from day1_handler import start_day1
from day2_handler import start_day2
from day3_handler import start_day3
from day4_handler import start_day4
from day5_handler import start_day5

router = Router()

# ===== Основные команды =====

import texts

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await db.create_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await message.answer_photo(photo=types.FSInputFile("img/Старт.png"))
    await message.answer(
        text=texts.START_TEXT,
        reply_markup=keyboards.main_menu_kb(),
    )

@router.message(F.text.in_({"Помощь", "/help"}))
async def btn_help(message: types.Message):
    await message.answer(USER_COMMANDS_TEXT, parse_mode=None)

@router.message(F.text == "Генератор мемов")
async def btn_meme_generator(message: types.Message):
    meme_folder = "img/mem"
    memes = [f for f in os.listdir(meme_folder) if os.path.isfile(os.path.join(meme_folder, f))]
    if not memes:
        await message.answer("Извините, мемы временно недоступны.")
        return
    
    random_meme = random.choice(memes)
    meme_path = os.path.join(meme_folder, random_meme)
    
    await message.answer_photo(
        photo=types.FSInputFile(meme_path),
        caption="Смех — лучший коммуникатор"
    )

@router.message(F.text == "Профиль")
async def btn_profile(message: types.Message):
    profile = await db.get_profile(message.from_user.id)
    if not profile:
        await message.answer("Профиль не найден. Нажмите /start, чтобы начать.", reply_markup=keyboards.main_menu_kb())
        return

    rewards_val = profile.get('rewards')
    rewards_list = json.loads(rewards_val) if isinstance(rewards_val, str) and rewards_val else (rewards_val if isinstance(rewards_val, list) else [])

    results_val = profile.get('results')
    results_list = json.loads(results_val) if isinstance(results_val, str) and results_val else (results_val if isinstance(results_val, list) else [])

    if await db.has_completed_all_days(message.from_user.id) and "Мастер коммуникаций" not in rewards_list:
        rewards_list.append("Мастер коммуникаций")
    
    results_text = "\n" + "\n".join([f"• {item}" for item in results_list]) if results_list else " 0"

    caption = (
        f"<b>Профиль:</b>\n"
        f"ID: <code>{profile['id']}</code>\n"
        f"Логин: {profile['username'] or '—'}\n"
        f"Баллы: {profile['points']}\n\n"
        f"<b>Результаты:</b>{results_text}"
    )

    show_rewards_buttons = False
    day5_progress = await db.get_day_progress(message.from_user.id, 5)
    if day5_progress:
        quiz_done = day5_progress.get("quiz_completed", False)
        reflection_done = day5_progress.get("reflection_completed", False)
        if quiz_done and reflection_done and profile.get('points', 0) >= 60:
            show_rewards_buttons = True

    await message.answer_photo(
        photo=types.FSInputFile("img/13.png"),
        caption=caption,
        reply_markup=keyboards.profile_kb(show_rewards=show_rewards_buttons)
    )

@router.callback_query(F.data == "get_certificate")
async def get_certificate_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    profile = await db.get_profile(user_id)
    day5_progress = await db.get_day_progress(user_id, 5)
    quiz_done = day5_progress.get("quiz_completed", False)
    reflection_done = day5_progress.get("reflection_completed", False)

    if quiz_done and reflection_done and profile.get('points', 0) >= 60:
        try:
            await callback.message.answer_photo(
                photo=types.FSInputFile("img/certificate/Сертификат_Мастер коммникаций.png"),
                caption="Поздравляем! Вот ваш сертификат."
            )
            await db.add_result(user_id, "Сертификат и стикеры")
            await callback.answer("Сертификат отправлен!")
        except Exception as e:
            logging.error(f"Failed to send certificate: {e}")
            await callback.answer("Не удалось отправить сертификат. Обратитесь к администратору.", show_alert=True)
    else:
        await callback.answer("Вы еще не выполнили условия для получения сертификата.", show_alert=True)


@router.callback_query(F.data.startswith("podcast:"))
async def send_podcast(callback: types.CallbackQuery):
    day = int(callback.data.split(":")[1])
    audio_path = f"audio/case{day}.mp3"
    try:
        await callback.message.answer_audio(
            audio=types.FSInputFile(audio_path),
            caption=f"Подкаст дня {day}"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Failed to send podcast for day {day}: {e}")
        await callback.answer("Не удалось отправить подкаст. Попробуйте позже.", show_alert=True)

# ===== Обработка дней =====

@router.message(F.text == "Выбрать день")
async def btn_select_day(message: types.Message):
    open_days = await db.get_open_days()
    await message.answer("Выберите день, чтобы посмотреть его контент:", reply_markup=keyboards.days_menu_kb(open_days))

@router.callback_query(F.data.startswith("select_day:"))
async def cb_select_day(callback: types.CallbackQuery, state: FSMContext):
    day = int(callback.data.split(":")[1])
    await db.create_user(callback.from_user.id, callback.from_user.username)

    day_starters = {
        1: start_day1,
        2: start_day2,
        3: start_day3,
        4: start_day4,
        5: start_day5,
    }
    
    starter = day_starters.get(day)
    if starter:
        await starter(callback.message, state)
    else:
        await callback.message.answer(f"День {day}: контент скоро будет доступен.")
    await callback.answer()

@router.callback_query(F.data == "day_locked")
async def cb_day_locked(callback: types.CallbackQuery):
    await callback.answer("Этот день еще не открыт.", show_alert=True)

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
        input_message_content=InputTextMessageContent(message_text=query_text),
        thumb_url="https://w7.pngwing.com/pngs/32/933/png-transparent-steel-industry-logo-severstal-industry-company-text-trademark.png",
    )
    
    await inline_query.answer([result], cache_time=1)

# ===== Админ-команды =====

@router.message(Command("ashelp"))
async def cmd_admin_help(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer(ADMIN_COMMANDS_TEXT, parse_mode=None)

@router.message(Command("addday"))
async def cmd_add_day(message: types.Message):
    if not is_admin(message.from_user.id): return
    opened_day = await db.open_next_day()
    if opened_day:
        await message.answer(f"✅ День {opened_day} успешно открыт!")
    else:
        await message.answer("⚠️ Все дни уже открыты.")

@router.message(Command("closeday"))
async def cmd_close_day(message: types.Message):
    if not is_admin(message.from_user.id): return
    closed_day = await db.close_last_day()
    if closed_day:
        await message.answer(f"✅ День {closed_day} успешно закрыт!")
    else:
        await message.answer("⚠️ Нельзя закрыть первый день или все дни уже закрыты.")

@router.message(Command("setday"))
async def cmd_set_day(message: types.Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Использование: /setday <номер_дня>")
        return
        
    day = int(args[1])
    if 1 <= day <= EVENT_DAYS:
        await db.set_current_day(day)
        await message.answer(f"✅ День установлен: {day}")
    else:
        await message.answer(f"⚠️ День должен быть в диапазоне 1-{EVENT_DAYS}.")

@router.message(Command("def"))
async def cmd_reset_progress(message: types.Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Использование: /def <user_id>")
        return
    
    user_id_to_reset = int(args[1])
    
    profile = await db.get_profile(user_id_to_reset)
    if not profile:
        await message.answer(f"Пользователь с ID {user_id_to_reset} не найден.")
        return

    await db.reset_user_progress(user_id_to_reset)
    await message.answer(f"✅ Прогресс для пользователя ID {user_id_to_reset} полностью сброшен.")

# ===== "Ловец" всех остальных сообщений =====

@router.message()
async def unknown_message(message: types.Message):
    await message.answer("Команда не распознана. Используйте меню или /help.")