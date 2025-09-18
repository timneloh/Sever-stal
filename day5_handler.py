import random
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

import db
import texts
import keyboards
from states import Day5States
from utils import safe_delete_message

router = Router()

async def start_day5(message: types.Message, state: FSMContext):
    storage_key: StorageKey = state.key
    user_id = storage_key.user_id

    await state.clear()
    await state.set_state(Day5States.QUIZ)
    await state.update_data(q_idx=0, correct_answers=0, user_id=user_id)
    await message.answer_photo(
        photo=types.FSInputFile("img/День 5.png"),
        caption=texts.DAY5_INTRO
    )
    await ask_day5_question(message, state)

async def ask_day5_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Удаляем предыдущие сообщения (если есть)
    for msg in data.get('sent_messages', []):
        await safe_delete_message(msg)
    await state.update_data(sent_messages=[])

    q_idx = data.get("q_idx", 0)
    
    if q_idx >= len(texts.DAY5_QUIZ_QUESTIONS):
        await show_day5_quiz_results(message, state)
        return

    question = texts.DAY5_QUIZ_QUESTIONS[q_idx]
    sent_message = await message.answer(
        f"<b>Вопрос {q_idx+1}/{len(texts.DAY5_QUIZ_QUESTIONS)}</b>\n{question['text']}",
        reply_markup=keyboards.day5_quiz_kb(question['options'])
    )
    await state.update_data(sent_messages=[sent_message])

async def show_day5_quiz_results(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    correct_answers = data.get("correct_answers", 0)

    # Проверяем, проходил ли пользователь квиз раньше
    progress = await db.get_day_progress(user_id, 5)
    if not progress.get("quiz_completed", False):
        await db.update_points(user_id, 20) # Баллы за квиз
        await db.update_day_progress_data(user_id, 5, {"quiz_completed": True})
        await message.answer(
            f"Квиз завершен!\nПравильных ответов: {correct_answers} из {len(texts.DAY5_QUIZ_QUESTIONS)}.\n"
            f"Вам начислено <b>+20 баллов!</b>",
            reply_markup=keyboards.day5_after_quiz_kb()
        )
    else:
        await message.answer(
            f"Квиз завершен!\nПравильных ответов: {correct_answers} из {len(texts.DAY5_QUIZ_QUESTIONS)}.",
            reply_markup=keyboards.day5_after_quiz_kb()
        )


@router.callback_query(Day5States.QUIZ, F.data.startswith("day5:answer:"))
async def handle_day5_answer(callback: types.CallbackQuery, state: FSMContext):
    answer_idx = int(callback.data.split(":")[-1])
    data = await state.get_data()
    q_idx = data.get("q_idx", 0)
    question = texts.DAY5_QUIZ_QUESTIONS[q_idx]

    await safe_delete_message(callback.message)

    if answer_idx == question["correct"]:
        await state.update_data(correct_answers=data.get("correct_answers", 0) + 1)
        feedback_text = f"✅ Верно!\n<i>{question['comment']}</i>"
    else:
        feedback_text = f"❌ Неверно. Правильный ответ: {question['options'][question['correct']]}\n<i>{question['comment']}</i>"

    next_q_idx = q_idx + 1
    if next_q_idx >= len(texts.DAY5_QUIZ_QUESTIONS):
        keyboard = keyboards.day5_finish_quiz_kb()
    else:
        keyboard = keyboards.day5_next_question_kb()

    await callback.message.answer(feedback_text, reply_markup=keyboard)
    await state.update_data(q_idx=next_q_idx)
    await callback.answer()

@router.callback_query(F.data == "day5:next_question")
async def handle_day5_next_question(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await ask_day5_question(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "day5:finish_quiz")
async def handle_day5_finish_quiz(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await show_day5_quiz_results(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "day5:start_reflection")
async def start_reflection(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Day5States.REFLECTION)
    await callback.message.answer(texts.DAY5_REFLECTION_PROMPT)
    await callback.answer()

@router.message(Day5States.REFLECTION)
async def handle_reflection(message: types.Message, state: FSMContext):
    # Проверяем, проходил ли пользователь рефлексию раньше
    progress = await db.get_day_progress(message.from_user.id, 5)
    if not progress.get("reflection_completed", False):
        await db.save_reflection(message.from_user.id, message.text)
        await db.update_points(message.from_user.id, 15)
        await db.mark_day_completed(message.from_user.id, 5)
        await db.update_day_progress_data(message.from_user.id, 5, {"reflection_completed": True})
        final_motivation = random.choice(texts.DAY5_FINAL_MOTIVATION_CARD_TEXTS)
        await db.add_result(message.from_user.id, final_motivation)
        
        await message.answer(
            "Спасибо за твой отзыв! Марафон завершен. Тебе начислено <b>+15 баллов.</b>\n\n"
            "Загляни в свой профиль, чтобы увидеть все результаты и награды!"
        )
        await state.clear()
        
        # Отправка финальной фотокарточки
        image_path = f"img/{final_motivation}.png"
        await message.answer_photo(
            photo=types.FSInputFile(image_path),
            caption=final_motivation
        )
    else:
        await message.answer("Вы уже прошли рефлексию.")
        await state.clear()

