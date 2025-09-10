import logging
import uuid
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


from config import EVENT_DAYS, ADMINS
import db
import texts
import keyboards
from commands import USER_COMMANDS_TEXT, ADMIN_COMMANDS_TEXT
from states import TestStates, Day2States, SERIOUS_INTRO

router = Router()
logging.basicConfig(level=logging.INFO)

current_day_global = 1  # активный день

# ===== Вспомогательные функции =====

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

async def to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню.", reply_markup=keyboards.main_menu_kb())

async def safe_delete_message(message: types.Message):
    try:
        await message.delete()
    except Exception as e:
        logging.debug(f"Не удалось удалить сообщение: {e}")

def parse_idx(cb_data: str) -> int | None:
    if ":" not in cb_data: return None
    _, num = cb_data.split(":", 1)
    return int(num) if num.isdigit() else None

# ===== Основные команды =====

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    db.create_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await message.answer(
        "Привет! Это бот «Неделя знаний Северсталь». Нажмите «Начать день», чтобы перейти к активностям.",
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
    rewards = ', '.join(profile['rewards']) or "Нет наград"
    await message.answer(
        f"<b>Профиль:</b>\nID: <code>{profile['id']}</code>\nЛогин: {profile['username'] or '—'}\nБаллы: {profile['points']}\nНаграды: {rewards}"
    )

# ===== Обработка дней =====

@router.message(F.text == "Начать день")
async def btn_start_day(message: types.Message, state: FSMContext):
    db.create_user(message.from_user.id, message.from_user.username)
    
    if current_day_global == 1:
        await start_day1(message, state)
    elif current_day_global == 2:
        await start_day2(message, state)
    else:
        await message.answer(
            f"День {current_day_global}: контент скоро будет доступен.",
            reply_markup=keyboards.back_to_menu_inline()
        )

@router.callback_query(F.data == "nav:main")
async def nav_main(callback: types.CallbackQuery, state: FSMContext):
    await to_main_menu(callback.message, state)
    await callback.answer()

# ===== ДЕНЬ 1: ТЕСТЫ =====

async def start_day1(message: types.Message, state: FSMContext):
    await state.set_state(TestStates.CHOOSE_TEST)
    await message.answer("День 1: выберите режим:", reply_markup=keyboards.day1_mode_kb())

@router.callback_query(F.data == "day1:choose_again", TestStates.CHOOSE_TEST)
async def day1_choose_again(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await start_day1(callback.message, state)
    await callback.answer()

# --- Серьёзный тест (DiSC) ---
def calculate_disc_profile(scores: dict) -> str:
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    leader, second = sorted_scores[0], sorted_scores[1]
    
    if leader[1] - second[1] >= 3:
        return leader[0]  # Чистый профиль
    else:
        # Комбинированный профиль
        profile = "".join(sorted([leader[0], second[0]]))
        return profile

async def show_disc_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    scores = data.get("disc_scores", {})
    profile = calculate_disc_profile(scores)
    result = texts.DISC_RESULTS.get(profile, texts.DISC_RESULTS["D"]) # 'D' как заглушка

    tips_text = "\n".join([f"🔸 {tip}" for tip in result['tips']])
    result_message = (
        f"<b>{result['title']}</b>\n"
        f"<i>{result['header']}</i>\n\n"
        f"{result['description']}\n\n"
        f"<b>Три практических совета:</b>\n{tips_text}"
    )
    
    share_text = f"Мой коммуникационный профиль по DiSC — {result['title']}. А какой у тебя? Пройди тест в боте «Неделя знаний Северсталь»!"
    await message.answer(result_message, reply_markup=keyboards.disc_result_kb(share_text))
    
    # Показываем мотивационную карточку
    motivational_card = texts.get_motivational_card(profile)
    await message.answer(f"✨ <i>{motivational_card}</i> ✨")

    uid = message.chat.id
    if not db.has_completed_day1(uid):
        db.update_points(uid, 10)
        db.mark_day1_completed(uid)
        await message.answer("🎉 Вам начислено <b>+10 баллов</b> за прохождение теста!")
    
    await state.set_state(TestStates.CHOOSE_TEST)


@router.callback_query(F.data == "day1:serious", TestStates.CHOOSE_TEST)
async def start_day1_serious(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await state.set_state(TestStates.SERIOUS_TEST)
    await state.update_data(disc_q=0, disc_scores={"D": 0, "i": 0, "S": 0, "C": 0})
    await callback.message.answer(SERIOUS_INTRO)
    await ask_next_disc_question(callback.message, state)
    await callback.answer()

async def ask_next_disc_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    qidx = data.get("disc_q", 0)

    if qidx >= len(texts.DISC_QUESTIONS):
        await show_disc_result(message, state)
        return

    q = texts.DISC_QUESTIONS[qidx]
    qtype = q.get("type")
    
    text = f"Вопрос {qidx + 1}/{len(texts.DISC_QUESTIONS)}\n<b>{q['text']}</b>"
    
    if qtype == "slider":
        text += f"\n\n<i>«{q['left']}» ↔ «{q['right']}»</i>"

    kb = None
    if qtype == "slider": kb = keyboards.slider_kb()
    elif qtype == "mc": kb = keyboards.mc_kb(q)
    elif qtype == "assoc": kb = keyboards.assoc_kb(q)
        
    if kb:
        await message.answer(text, reply_markup=kb)
    else: # Пропускаем некорректный вопрос
        await state.update_data(disc_q=qidx + 1)
        await ask_next_disc_question(message, state)

@router.callback_query(TestStates.SERIOUS_TEST)
async def handle_disc_answer(callback: types.CallbackQuery, state: FSMContext):
    if ":" not in callback.data:
        await callback.answer("Пожалуйста, нажмите на одну из кнопок с вариантом ответа.")
        return

    await safe_delete_message(callback.message)
    data = await state.get_data()
    qidx = data.get("disc_q", 0)
    q = texts.DISC_QUESTIONS[qidx]
    scores = data.get("disc_scores")
    
    answer_type, answer_idx = callback.data.split(":", 1)
    answer_idx = int(answer_idx)

    inc = {}
    if answer_type == "slider":
        inc = {q["cat_l"]: 6 - answer_idx, q["cat_r"]: answer_idx}
    elif answer_type == "mc":
        cats = [opt[1] for opt in q["options"]]
        inc = {c: 1 for c in cats}
        inc[cats[answer_idx]] += 4
    elif answer_type == "assoc":
        cats = q["cats"]
        inc = {c: 1 for c in cats}
        inc[cats[answer_idx]] += 4

    for k, v in inc.items():
        scores[k] += v

    await state.update_data(disc_scores=scores, disc_q=qidx + 1)
    await ask_next_disc_question(callback.message, state)
    await callback.answer()

# --- Шуточный тест ---
async def show_fun_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    scores = data.get("fun_scores", {})
    if not scores:
        archetype_key = "РАЦИЯ_БЕЗ_БАТАРЕЕК"
    else:
        archetype_key = max(scores, key=scores.get)
    
    result = texts.FUN_RESULTS[archetype_key]
    
    result_message = (
        f"<b>Твоё альтер-эго: {result['title']}</b>\n\n"
        f"{result['description']}\n\n"
        f"{result['tip']}"
    )
    share_text = f"{result['share']} А какой у тебя? Пройди тест в боте «Неделя знаний Северсталь»!"
    await message.answer(result_message, reply_markup=keyboards.fun_result_kb(share_text))
    
    uid = message.chat.id
    if not db.has_completed_day1(uid):
        db.update_points(uid, 10)
        db.mark_day1_completed(uid)
        await message.answer("🎉 Вам начислено <b>+10 баллов</b> за прохождение теста!")
        
    await state.set_state(TestStates.CHOOSE_TEST)


@router.callback_query(F.data == "day1:fun", TestStates.CHOOSE_TEST)
async def start_day1_fun(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await state.set_state(TestStates.FUN_TEST)
    scores = {archetype: 0 for archetype in texts.ARCHETYPES}
    await state.update_data(fun_q=0, fun_scores=scores)
    await callback.message.answer(texts.FUN_TEST_INTRO)
    await ask_next_fun_question(callback.message, state)
    await callback.answer()

async def ask_next_fun_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    qidx = data.get("fun_q", 0)

    if qidx >= len(texts.FUN_QUESTIONS):
        await show_fun_result(message, state)
        return

    q = texts.FUN_QUESTIONS[qidx]
    text = f"Вопрос {qidx + 1}/{len(texts.FUN_QUESTIONS)}\n<b>{q['text']}</b>"
    await message.answer(text, reply_markup=keyboards.fun_test_kb(q))

@router.callback_query(TestStates.FUN_TEST, F.data.startswith("fun:"))
async def handle_fun_answer(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    data = await state.get_data()
    qidx = data.get("fun_q", 0)
    q = texts.FUN_QUESTIONS[qidx]
    scores = data.get("fun_scores")

    sel_idx = parse_idx(callback.data)
    
    for i, option in enumerate(q["options"]):
        archetype = option[1]
        if i == sel_idx:
            scores[archetype] += 5
        else:
            scores[archetype] += 1
            
    await state.update_data(fun_scores=scores, fun_q=qidx + 1)
    await ask_next_fun_question(callback.message, state)
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

# ===== ДЕНЬ 2: КАРТОЧКИ =====

async def start_day2(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    progress = db.get_day2_progress(uid)

    if progress["completed"]:
        await message.answer(
            "Ты уже открыл все карточки сегодня. Отличная работа! Возвращайся завтра.",
            reply_markup=keyboards.back_to_menu_inline()
        )
        return

    await state.set_state(Day2States.CHOOSE_CARD)
    
    text = texts.DAY2_INTRO
    if progress["opened_cards"]:
        text = f"Продолжим! У тебя осталось {5 - len(progress['opened_cards'])} карточек на сегодня."

    await message.answer(text, reply_markup=keyboards.day2_cards_kb(progress['opened_cards']))

@router.callback_query(Day2States.CHOOSE_CARD, F.data.startswith("day2:card:"))
async def handle_day2_card(callback: types.CallbackQuery, state: FSMContext):
    card_idx = parse_idx(callback.data)
    uid = callback.from_user.id
    
    db.update_points(uid, 3)
    db.mark_day2_card_opened(uid, card_idx)
    
    card = texts.DAY2_CARDS[card_idx]
    card_text = (
        f"<b>{card['title']}</b>\n"
        f"<i>{card['quote']}</i>\n\n"
        f"{card['compliment']}\n"
        f"{card['task']}"
    )
    
    await callback.message.answer_photo(
        photo="https://placehold.co/600x400/2E2E2E/FFFFFF?text=Day+2", # Заглушка для фото
        caption=card_text
    )
    await callback.message.answer("✅ Отлично! <b>+3 балла</b> добавлены в твой профиль.")
    
    # Обновляем клавиатуру
    await safe_delete_message(callback.message)
    await start_day2(callback.message, state)
    await callback.answer()

@router.callback_query(Day2States.CHOOSE_CARD, F.data == "day2:opened")
async def handle_day2_opened_card(callback: types.CallbackQuery):
    await callback.answer("Эта карточка уже открыта.", show_alert=True)

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
        await message.answer("Использование: /setday &lt;номер_дня&gt;")
        return
        
    day = int(args[1])
    global current_day_global
    if 1 <= day <= EVENT_DAYS:
        current_day_global = day
        await message.answer(f"✅ День установлен: {current_day_global}")
    else:
        await message.answer(f"⚠️ День должен быть в диапазоне 1-{EVENT_DAYS}.")

# ===== "Ловец" всех остальных сообщений =====

@router.message()
async def unknown_message(message: types.Message):
    await message.answer("Команда не распознана. Используйте меню или /help.")

