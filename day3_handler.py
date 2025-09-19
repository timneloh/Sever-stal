from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import db
import texts
import keyboards
from states import Day3States
from utils import safe_delete_message
import logging


router = Router()

async def start_day3(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Day3States.CHOOSE_HERO)
    await state.update_data(hero_idx=0)
    await message.answer_photo(
        photo=types.FSInputFile("img/День 3.png"),
        caption=texts.DAY3_INTRO
    )
    await show_hero_card(message, state)

async def show_hero_card(message: types.Message, state: FSMContext, message_id_to_edit: int = None):
    data = await state.get_data()
    hero_idx = data.get("hero_idx", 0)
    
    heroes_keys = list(texts.DAY3_HEROES.keys())
    hero_key = heroes_keys[hero_idx]
    hero_info = texts.DAY3_HEROES[hero_key]

    caption = f"<b>{hero_info['name']}</b>\n<i>{hero_info['description']}</i>"
    
    if message_id_to_edit:
        await message.bot.edit_message_media(
            media=types.InputMediaPhoto(media=types.FSInputFile(hero_info['img']), caption=caption),
            chat_id=message.chat.id,
            message_id=message_id_to_edit,
            reply_markup=keyboards.day3_hero_select_kb(heroes_keys, hero_idx)
        )
    else:
        await message.answer_photo(
            photo=types.FSInputFile(hero_info['img']),
            caption=caption,
            reply_markup=keyboards.day3_hero_select_kb(heroes_keys, hero_idx)
        )

@router.callback_query(Day3States.CHOOSE_HERO, F.data.startswith("day3:hero_nav:"))
async def nav_hero(callback: types.CallbackQuery, state: FSMContext):
    new_idx = int(callback.data.split(":")[-1])
    await state.update_data(hero_idx=new_idx)
    await show_hero_card(callback.message, state, message_id_to_edit=callback.message.message_id)
    await callback.answer()

@router.callback_query(Day3States.CHOOSE_HERO, F.data.startswith("day3:hero_choose:"))
async def choose_hero(callback: types.CallbackQuery, state: FSMContext):
    hero_key = callback.data.split(":")[-1]
    await state.set_state(Day3States.COMICS_PROGRESS)
    await state.update_data(
        hero=hero_key, 
        frame=0, 
        scores={"сила": 0, "мягкость": 0, "харизма": 0}
    )
    await safe_delete_message(callback.message)
    await ask_comics_question(callback.message, state)
    await callback.answer()

async def ask_comics_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    hero = data.get("hero")
    frame_idx = data.get("frame", 0)
    
    comics_frames = texts.DAY3_COMICS.get(hero, [])
    
    if frame_idx >= len(comics_frames) or not comics_frames[frame_idx]['choices']:
        # Комикс завершен
        await show_comics_result(message, state)
        return

    frame_data = comics_frames[frame_idx]
    
    await message.answer_photo(
        photo=types.FSInputFile(frame_data['img']),
        caption=f"{frame_data['text']}\n\n<i>Кадр {frame_idx+1}/{len(comics_frames)}</i>",
        reply_markup=keyboards.day3_comics_choice_kb(frame_data['choices'])
    )

async def show_comics_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    hero = data.get("hero")
    scores = data.get("scores")
    uid = message.chat.id

    # Улучшенная логика определения доминирующей черты с обработкой ничьей
    if not scores or not any(s > 0 for s in scores.values()):
        dominant_trait = 'default'
    else:
        max_score = max(scores.values())
        top_traits = [trait for trait, score in scores.items() if score == max_score]

        if len(top_traits) == 1:
            dominant_trait = top_traits[0]
        else: # len(top_traits) > 1, т.е. ничья
            priority = ['сила', 'харизма', 'мягкость']
            # Ищем первую черту из приоритетного списка, которая есть в списке лидеров
            for trait in priority:
                if trait in top_traits:
                    dominant_trait = trait
                    break
            else:
                # Этот блок выполнится, если ни одна из черт в priority не найдена в top_traits,
                # что маловероятно, но является хорошей защитой.
                dominant_trait = 'default'

    # Получаем текст концовки
    ending_text = texts.DAY3_COMICS[hero][-1]['endings'][dominant_trait]
    image_path = f"img/comics/{hero}_ending_{dominant_trait}.png"

    try:
        await message.answer_photo(
            photo=types.FSInputFile(image_path),
            caption=ending_text,
            reply_markup=keyboards.day3_after_comics_kb()
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить фото {image_path}: {e}. Отправляю текстом.")
        await message.answer(ending_text, reply_markup=keyboards.day3_after_comics_kb())

    # Новая логика начисления баллов
    day3_progress = await db.get_day_progress(uid, 3)
    completed_heroes = day3_progress.get("completed_heroes", [])

    if hero not in completed_heroes:
        await db.update_points(uid, 5)  # Баллы за прохождение комикса
        await message.answer("🎉 Вам начислено <b>+5 баллов</b> за прохождение истории!")
        
        # Обновляем прогресс в БД
        completed_heroes.append(hero)
        await db.update_day_progress_data(uid, 3, {"completed_heroes": completed_heroes})

@router.callback_query(Day3States.COMICS_PROGRESS, F.data.startswith("day3:comics_choice:"))
async def handle_comics_choice(callback: types.CallbackQuery, state: FSMContext):
    choice_idx = int(callback.data.split(":")[-1])
    data = await state.get_data()
    
    hero = data.get("hero")
    frame_idx = data.get("frame", 0)
    scores = data.get("scores")
    
    frame_data = texts.DAY3_COMICS[hero][frame_idx]
    choice_scores = frame_data['choices'][choice_idx][1]
    
    for key, value in choice_scores.items():
        scores[key] += value
        
    await state.update_data(scores=scores, frame=frame_idx + 1)
    await safe_delete_message(callback.message)
    await ask_comics_question(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "day3:choose_another_hero")
async def choose_another_hero_handler(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    await start_day3(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "day3:start_quiz")
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Day3States.QUIZ)
    await state.update_data(quiz_q=0, quiz_score=0)
    await safe_delete_message(callback.message)
    await ask_quiz_question(callback.message, state)
    await callback.answer()

async def ask_quiz_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_idx = data.get("quiz_q", 0)
    
    if q_idx >= len(texts.DAY3_QUIZ["questions"]):
        await show_quiz_result(message, state)
        return
        
    q_data = texts.DAY3_QUIZ["questions"][q_idx]
    await message.answer(
        f"<b>Вопрос {q_idx+1}:</b>\n{q_data['text']}",
        reply_markup=keyboards.day3_quiz_kb(q_data['options'])
    )
    
async def show_quiz_result(message: types.Message, state: FSMContext):
    # Тут логика определения архетипа по баллам викторины
    archetype = "Лидер-стратег" # Заглушка
    await message.answer(f"Викторина пройдена!\nВаш архетип: <b>{archetype}</b>", reply_markup=keyboards.back_to_menu_inline())

    uid = message.chat.id
    if not await db.has_completed_day(uid, 3):
        await db.mark_day_completed(uid, 3)
        await db.add_result(uid, archetype)
        await message.answer("День 3 пройден!")
        
@router.callback_query(Day3States.QUIZ, F.data.startswith("day3:quiz_answer:"))
async def handle_quiz_answer(callback: types.CallbackQuery, state: FSMContext):
    # (Здесь должна быть логика проверки ответа, начисления баллов)
    await state.update_data(quiz_q=(await state.get_data()).get("quiz_q", 0) + 1)
    await safe_delete_message(callback.message)
    await ask_quiz_question(callback.message, state)
    await callback.answer()
