from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random

import db
import texts
from states import Day4States
from utils import safe_delete_message

router = Router()

def watched_video_kb(case_idx: int):
    """Создает клавиатуру с кнопкой 'Посмотрел'."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Посмотрел", callback_data=f"day4:watched:{case_idx}")]
        ]
    )
    return keyboard

def day4_quiz_kb(options: list, case_idx: int):
    """Создает клавиатуру с вариантами ответа для викторины 4-го дня."""
    buttons = [
        [InlineKeyboardButton(text=option, callback_data=f"day4:answer:{case_idx}:{i}")]
        for i, option in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def start_day4(message: types.Message, state: FSMContext):
    """Запускает активности 4-го дня."""
    await state.clear()
    await state.set_state(Day4States.WATCHING_VIDEO)
    await state.update_data(case_idx=0, sent_messages=[])

    await message.answer_photo(
        photo=types.FSInputFile("img/День 4.png"),
        caption=texts.DAY4_INTRO
    )
    await send_day4_video(message, state)

async def send_day4_video(message: types.Message, state: FSMContext):
    """Отправляет видео для текущего кейса."""
    data = await state.get_data()
    case_idx = data.get("case_idx", 0)
    
    if case_idx >= len(texts.DAY4_CASES):
        # Все кейсы пройдены
        await message.answer(random.choice(texts.DAY4_FINAL_MOTIVATION))
        db.mark_day_completed(message.from_user.id, 4)
        db.add_result(message.from_user.id, "Тренер интонации")
        await state.clear()
        return

    case = texts.DAY4_CASES[case_idx]
    
    # Отправка видео с кнопкой "Посмотрел"
    sent_message = await message.answer_video(
        video=types.FSInputFile(case['video']),
        caption=f"<b>{case['title']}</b>",
        reply_markup=watched_video_kb(case_idx)
    )
    # Сохраняем весь объект сообщения, а не только его ID
    await state.update_data(sent_messages=data.get('sent_messages', []) + [sent_message])


@router.callback_query(Day4States.WATCHING_VIDEO, F.data.startswith("day4:watched:"))
async def handle_watched_video(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки 'Посмотрел'."""
    data = await state.get_data()
    
    # Удаляем предыдущие сообщения (включая видео и прошлый фидбэк)
    for msg in data.get('sent_messages', []):
        await safe_delete_message(msg)
    await state.update_data(sent_messages=[])

    await callback.answer("Отлично! Теперь ответьте на вопрос.")
    await state.set_state(Day4States.QUIZ)
    await ask_day4_question(callback.message, state)


async def ask_day4_question(message: types.Message, state: FSMContext):
    """Задает вопрос для текущего кейса."""
    data = await state.get_data()
    case_idx = data.get("case_idx", 0)
    case = texts.DAY4_CASES[case_idx]

    question_text = "Что было не так в этой переписке?"
    
    sent_message = await message.answer(
        question_text,
        reply_markup=day4_quiz_kb(case['options'], case_idx)
    )
    # Сохраняем весь объект сообщения
    await state.update_data(sent_messages=data.get('sent_messages', []) + [sent_message])


@router.callback_query(Day4States.QUIZ, F.data.startswith("day4:answer:"))
async def handle_day4_answer(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответ пользователя на вопрос викторины."""
    _, _, case_idx_str, answer_idx_str = callback.data.split(":")
    case_idx = int(case_idx_str)
    answer_idx = int(answer_idx_str)
    
    data = await state.get_data()
    
    # Удаляем предыдущие сообщения (только сообщение с вопросом)
    for msg in data.get('sent_messages', []):
        await safe_delete_message(msg)
    await state.update_data(sent_messages=[])

    if case_idx != data.get("case_idx"):
        await callback.answer("Этот вопрос уже неактуален.", show_alert=True)
        return

    case = texts.DAY4_CASES[case_idx]

    feedback_message = None # Переменная для хранения сообщения с фидбэком

    if answer_idx == case["correct"]:
        feedback_message = await callback.message.answer(f"✅ Да, это правильный вариант!\n\n<i>{case['comment']}</i>")
        await db.update_points(callback.from_user.id, 3)
    else:
        correct_answer_text = case['options'][case['correct']]
        feedback_message = await callback.message.answer(f"❌ Этот ответ не правильный, правильный ответ: «{correct_answer_text}»\n\n<i>{case['comment']}</i>")
    
    # ⭐ ИЗМЕНЕНИЕ ЗДЕСЬ: Сохраняем сообщение с фидбэком в состояние, чтобы удалить его на следующем шаге
    if feedback_message:
        await state.update_data(sent_messages=[feedback_message])
        
    await state.update_data(case_idx=case_idx + 1)
    await state.set_state(Day4States.WATCHING_VIDEO)
    await send_day4_video(callback.message, state)
    await callback.answer()