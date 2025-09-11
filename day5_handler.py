from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import db
import texts
import keyboards
from states import Day5States
from utils import safe_delete_message

router = Router()

async def start_day5(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Day5States.QUIZ)
    await state.update_data(q_idx=0, correct_answers=0)
    await message.answer_photo(
        photo=types.FSInputFile("img/День 5.png"),
        caption=texts.DAY5_INTRO
    )
    await ask_day5_question(message, state)

async def ask_day5_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_idx = data.get("q_idx", 0)
    
    if q_idx >= len(texts.DAY5_QUIZ_QUESTIONS):
        await show_day5_quiz_results(message, state)
        return

    question = texts.DAY5_QUIZ_QUESTIONS[q_idx]
    await message.answer(
        f"<b>Вопрос {q_idx+1}/{len(texts.DAY5_QUIZ_QUESTIONS)}</b>\n{question['text']}",
        reply_markup=keyboards.day5_quiz_kb(question['options'])
    )

async def show_day5_quiz_results(message: types.Message, state: FSMContext):
    data = await state.get_data()
    correct_answers = data.get("correct_answers", 0)
    
    db.update_points(message.from_user.id, 20) # Баллы за квиз
    
    await message.answer(
        f"Квиз завершен!\nПравильных ответов: {correct_answers} из {len(texts.DAY5_QUIZ_QUESTIONS)}.\n"
        f"Вам начислено <b>+20 баллов!</b>",
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
        await callback.message.answer(f"✅ Верно!\n<i>{question['comment']}</i>")
    else:
        await callback.message.answer(f"❌ Неверно. Правильный ответ: {question['options'][question['correct']]}\n<i>{question['comment']}</i>")
        
    await state.update_data(q_idx=q_idx + 1)
    await ask_day5_question(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "day5:start_reflection")
async def start_reflection(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Day5States.REFLECTION)
    await callback.message.answer(texts.DAY5_REFLECTION_PROMPT)
    await callback.answer()

@router.message(Day5States.REFLECTION)
async def handle_reflection(message: types.Message, state: FSMContext):
    await db.save_reflection(message.from_user.id, message.text)
    await db.update_points(message.from_user.id, 15)
    await db.mark_day_completed(message.from_user.id, 5)
    await db.add_result(message.from_user.id, texts.DAY5_FINAL_MOTIVATION)
    
    await message.answer(
        "Спасибо за твой отзыв! Марафон завершен. Тебе начислено <b>+15 баллов.</b>\n\n"
        "Загляни в свой профиль, чтобы увидеть все результаты и награды!"
    )
    await state.clear()
    
    # Отправка финальной фотокарточки
    await message.answer_photo(
        photo=types.FSInputFile("img/Мастер коммуникации.png"),
        caption=texts.DAY5_FINAL_MOTIVATION
    )
