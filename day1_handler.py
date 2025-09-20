import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import db
import texts
import keyboards
from states import TestStates
from utils import safe_delete_message # Импортируем из общего хендлера

router = Router()

def parse_idx(cb_data: str) -> int | None:
    if ":" not in cb_data: return None
    _, num = cb_data.split(":", 1)
    return int(num) if num.isdigit() else None
    
# ===== ДЕНЬ 1: ТЕСТЫ =====

async def start_day1(message: types.Message, state: FSMContext):
    await state.set_state(TestStates.CHOOSE_TEST)
    await message.answer_photo(
        photo=types.FSInputFile("img/День 1.png"),
        caption="День 1: выберите режим:",
        reply_markup=keyboards.day1_mode_kb()
    )

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
        return leader[0]
    else:
        profile = "".join(sorted([leader[0], second[0]]))
        return profile

async def show_disc_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    scores = data.get("disc_scores", {})
    profile = calculate_disc_profile(scores)
    result = texts.DISC_RESULTS.get(profile, texts.DISC_RESULTS["D"])

    tips_text = "\n".join([f"🔸 {tip}" for tip in result['tips']])
    result_message = (
        f"<b>{result['title']}</b>\n"
        f"<i>{result['header']}</i>\n\n"
        f"{result['description']}\n\n"
        f"<b>Три практических совета:</b>\n{tips_text}"
    )
    
    share_text = f"Мой коммуникационный профиль по DiSC — {result['title']}. А какой у тебя? Пройди тест в боте «Неделя знаний Северсталь»!"
    
    # Формируем путь к изображению в зависимости от профиля
    if len(profile) == 1:
        image_path = f"img/Мотивация после теста {profile}.png"
    else:
        # Для комбинированных профилей (e.g., "DS" -> "Ds")
        profile_filename = profile[0] + profile[1].lower()
        image_path = f"img/Комбинированные профили {profile_filename}.png"

    try:
        await message.answer_photo(
            photo=types.FSInputFile(image_path),
            caption=result_message,
            reply_markup=keyboards.disc_result_kb(share_text)
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить фото {image_path}: {e}. Отправляю текстом.")
        await message.answer(result_message, reply_markup=keyboards.disc_result_kb(share_text))

    uid = message.chat.id
    await db.add_result(uid, result['title']) # Сохраняем результат
    if not await db.has_completed_day(uid, 1):
        await db.update_points(uid, 10)
        await db.mark_day_completed(uid, 1)
        await message.answer("🎉 Вам начислено <b>+10 баллов</b> за прохождение теста!")
    
    await state.set_state(TestStates.CHOOSE_TEST)



@router.callback_query(F.data == "day1:serious", TestStates.CHOOSE_TEST)
async def start_day1_serious(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await state.set_state(TestStates.SERIOUS_TEST)
    await state.update_data(disc_q=0, disc_scores={"D": 0, "i": 0, "S": 0, "C": 0})
    await callback.message.answer_photo(
        photo=types.FSInputFile("img/DiSC тест.png"),
        caption=texts.SERIOUS_INTRO
    )
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
    elif qtype == "mc":
        options_text = "\n".join([f"{i+1}. {opt[0]}" for i, opt in enumerate(q["options"])])
        text += f"\n\n{options_text}"
    elif qtype == "assoc":
        options_text = "\n".join([f"{i+1}. {icon}" for i, icon in enumerate(q["icons"])])
        text += f"\n\n{options_text}"


    kb = None
    if qtype == "slider": kb = keyboards.slider_kb()
    elif qtype == "mc": kb = keyboards.mc_kb(q)
    elif qtype == "assoc": kb = keyboards.assoc_kb(q)
        
    if kb:
        await message.answer(text, reply_markup=kb)
    else:
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
    
    answer_type, answer_idx_str = callback.data.split(":", 1)
    
    try:
        answer_idx = int(answer_idx_str)
    except ValueError:
        logging.warning(f"Некорректный callback_data: {callback.data}")
        return

    inc = {}
    if answer_type == "slider":
        # Логика баллов для слайдера: 1 -> 5:1, 2 -> 4:2, 3 -> 3:3, 4 -> 2:4, 5 -> 1:5
        inc = {q["cat_l"]: 6 - answer_idx, q["cat_r"]: answer_idx}
    elif answer_type == "mc":
        # Логика баллов для MC: выбранный +5, остальные +1
        cats = [opt[1] for opt in q["options"]]
        for i, cat in enumerate(cats):
            scores[cat] += 5 if i == answer_idx else 1
    elif answer_type == "assoc":
        # Логика баллов для Ассоциаций: выбранный +5, остальные +1
        cats = q["cats"]
        for i, cat in enumerate(cats):
            scores[cat] += 5 if i == answer_idx else 1

    if inc: # Только для слайдера, для MC/Assoc уже обновили
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
    
    image_filename = texts.ARCHETYPE_IMAGES.get(archetype_key, "заглушка.png")
    image_path = f"img/joke-test/{image_filename}"

    try:
        await message.answer_photo(
            photo=types.FSInputFile(image_path),
            caption=result_message,
            reply_markup=keyboards.fun_result_kb(share_text)
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить фото {image_path}: {e}. Отправляю текстом.")
        await message.answer(result_message, reply_markup=keyboards.fun_result_kb(share_text))

    uid = message.chat.id
    await db.add_result(uid, result['title']) # Сохраняем результат
    if not await db.has_completed_day(uid, 1):
        await db.update_points(uid, 10)
        await db.mark_day_completed(uid, 1)
        await message.answer("🎉 Вам начислено <b>+10 баллов</b> за прохождение теста!")
        
    await state.set_state(TestStates.CHOOSE_TEST)


@router.callback_query(F.data == "day1:fun", TestStates.CHOOSE_TEST)
async def start_day1_fun(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await state.set_state(TestStates.FUN_TEST)
    scores = {archetype: 0 for archetype in texts.ARCHETYPES}
    await state.update_data(fun_q=0, fun_scores=scores)
    await callback.message.answer_photo(
        photo=types.FSInputFile("img/joke-test/Шуточный тест.png"),
        caption=texts.FUN_TEST_INTRO
    )
    await ask_next_fun_question(callback.message, state)
    await callback.answer()

async def ask_next_fun_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    qidx = data.get("fun_q", 0)

    if qidx >= len(texts.FUN_QUESTIONS):
        await show_fun_result(message, state)
        return

    q = texts.FUN_QUESTIONS[qidx]
    options_text = "\n".join([f"{i+1}. {opt[0]}" for i, opt in enumerate(q["options"])])
    text = f"Вопрос {qidx + 1}/{len(texts.FUN_QUESTIONS)}\n<b>{q['text']}</b>\n\n{options_text}"
    await message.answer(text, reply_markup=keyboards.fun_test_kb(q))

@router.callback_query(TestStates.FUN_TEST, F.data.startswith("fun:"))
async def handle_fun_answer(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    data = await state.get_data()
    qidx = data.get("fun_q", 0)
    q = texts.FUN_QUESTIONS[qidx]
    scores = data.get("fun_scores")

    sel_idx = parse_idx(callback.data)
    
    # Логика баллов: выбранный +5, остальные +1
    for i, option in enumerate(q["options"]):
        archetype = option[1]
        scores[archetype] += 5 if i == sel_idx else 1
            
    await state.update_data(fun_scores=scores, fun_q=qidx + 1)
    await ask_next_fun_question(callback.message, state)
    await callback.answer()
