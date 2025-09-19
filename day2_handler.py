import json
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import db
import texts
import keyboards
from states import Day2States
from utils import safe_delete_message # Импортируем из общего хендлера

router = Router()

def parse_idx(cb_data: str) -> int | None:
    parts = cb_data.split(":")
    if not parts:
        return None
    num_str = parts[-1]
    return int(num_str) if num_str.isdigit() else None
    
# ===== ДЕНЬ 2: КАРТОЧКИ =====

async def start_day2(user_id: int, message: types.Message, state: FSMContext, edit_message: bool = False):
    progress = await db.get_day_progress(user_id, 2)
    opened_cards = progress.get("cards_opened", [])

    # --- Логика для финального сообщения (показывается один раз) ---
    if len(opened_cards) >= 5 and not progress.get("final_message_shown", False):
        try:
            # Отправляем финальное сообщение без кнопок
            await message.answer_photo(
                photo=types.FSInputFile("img/Мотивационная карточка-5.png"),
                caption=texts.DAY2_ALL_CARDS_OPENED
            )
            # Устанавливаем флаг, что сообщение было показано
            await db.update_day_progress_data(user_id, 2, {"final_message_shown": True})
        except Exception as e:
            logging.warning(f"Не удалось отправить финальное фото Дня 2: {e}")
            await message.answer(texts.DAY2_ALL_CARDS_OPENED)

        # Отмечаем день пройденным, если еще не отмечен
        if not await db.has_completed_day(user_id, 2):
            await db.mark_day_completed(user_id, 2)
    
    # --- Всегда показываем меню Дня 2 ---
    await state.set_state(Day2States.CHOOSE_CARD)
    if not opened_cards: # Добавляем результат только при первом входе в день
        await db.add_result(user_id, "Мотивационная карточка дня")

    caption_text = texts.DAY2_INTRO
    if opened_cards:
        caption_text = f"Продолжим! У тебя осталось {5 - len(opened_cards)} карточек на сегодня.\n\n" + caption_text

    media = types.InputMediaPhoto(
        media=types.FSInputFile("img/День 2.png"),
        caption=caption_text
    )
    reply_markup = keyboards.day2_cards_kb(opened_cards)

    try:
        if edit_message:
            await message.edit_media(media=media, reply_markup=reply_markup)
        else:
            await message.answer_photo(photo=media.media, caption=media.caption, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Day 2 - Failed to show menu: {e}")
        try:
            await message.answer_photo(photo=media.media, caption=media.caption, reply_markup=reply_markup)
        except Exception as e2:
            logging.error(f"Day 2 - Fallback failed: {e2}")


@router.callback_query(Day2States.CHOOSE_CARD, F.data.startswith("day2:card:"))
async def handle_day2_card(callback: types.CallbackQuery, state: FSMContext):
    card_idx = parse_idx(callback.data)
    if card_idx is None:
        await callback.answer("Ошибка: неверный ID карточки.", show_alert=True)
        return

    uid = callback.from_user.id

    # Получаем текущий прогресс
    progress = await db.get_day_progress(uid, 2)
    opened_cards = progress.get("cards_opened", [])

    if card_idx in opened_cards:
        await callback.answer("Эта карточка уже была открыта.", show_alert=True)
        return

    # Обновляем список открытых карточек и сохраняем в БД
    opened_cards.append(card_idx)
    await db.update_day_progress_data(uid, 2, {"cards_opened": opened_cards})
    
    # Начисляем баллы
    await db.update_points(uid, 3)
    
    card = texts.DAY2_CARDS[card_idx]
    # Объединяем текст карточки и уведомление о баллах
    card_text = (
        f"<b>{card['title']}</b>\n"
        f"<i>{card['quote']}</i>\n\n"
        f"{card['compliment']}\n"
        f"{card['task']}\n\n"
        f"✅ Отлично! <b>+3 балла</b> добавлены в твой профиль."
    )
    
    if card_idx == 0:
        photo_path = "img/Мотивационная карточка.png"
    else:
        photo_path = f"img/Мотивационная карточка-{card_idx}.png"

    try:
        # Редактируем медиа, заменяя меню на карточку
        await callback.message.edit_media(
            media=types.InputMediaPhoto(
                media=types.FSInputFile(photo_path),
                caption=card_text
            ),
            reply_markup=keyboards.day2_after_card_kb()
        )
    except Exception as e:
        logging.error(f"Day 2 - Failed to edit message to show card {card_idx}: {e}")
        await callback.message.answer("Произошла ошибка при отображении карточки. Попробуйте снова.")

    await callback.answer()


@router.callback_query(F.data == "day2:back_to_cards")
async def back_to_cards(callback: types.CallbackQuery, state: FSMContext):
    # Передаем правильный ID пользователя
    await start_day2(callback.from_user.id, callback.message, state, edit_message=True)
    await callback.answer()

@router.callback_query(Day2States.CHOOSE_CARD, F.data == "day2:opened")
async def handle_day2_opened_card(callback: types.CallbackQuery):
    await callback.answer("Эта карточка уже открыта.", show_alert=True)

@router.callback_query(F.data == "day2:empathy_test")
async def empathy_test(callback: types.CallbackQuery):
    await callback.message.answer(texts.EMPATHY_TEST_TEXT, reply_markup=keyboards.empathy_test_kb())
    await callback.answer()
