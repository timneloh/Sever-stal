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

async def start_day2(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    progress_str = await db.get_day_progress(uid, 2)
    progress = json.loads(progress_str) if isinstance(progress_str, str) else progress_str
    opened_cards = progress.get("cards_opened", [])

    # Проверяем, открыты ли все 5 основных карточек
    if len(opened_cards) >= 5:
        # Если все 5 открыты, показываем финальную 6-ю карточку
        try:
            await message.answer_photo(
                photo=types.FSInputFile("img/Мотивационная карточка-5.png"),
                caption=texts.DAY2_ALL_CARDS_OPENED,
                reply_markup=keyboards.back_to_menu_inline()
            )
        except Exception as e:
            logging.warning(f"Не удалось отправить фото img/Мотивационная карточка-5.png: {e}. Отправляю текстом.")
            await message.answer(
                texts.DAY2_ALL_CARDS_OPENED,
                reply_markup=keyboards.back_to_menu_inline()
            )



        # Отмечаем день пройденным, если еще не отмечен
        if not await db.has_completed_day(uid, 2):
            await db.mark_day_completed(uid, 2)
        return

    # Если еще не все карточки открыты, продолжаем обычную логику
    await state.set_state(Day2States.CHOOSE_CARD)
    await db.add_result(uid, "Мотивационная карточка дня")

    caption_text = texts.DAY2_INTRO
    if opened_cards:
        caption_text = f"Продолжим! У тебя осталось {5 - len(opened_cards)} карточек на сегодня.\n\n" + caption_text

    await message.answer_photo(
        photo=types.FSInputFile("img/День 2.png"),
        caption=caption_text,
        reply_markup=keyboards.day2_cards_kb(opened_cards)
    )


@router.callback_query(Day2States.CHOOSE_CARD, F.data.startswith("day2:card:"))
async def handle_day2_card(callback: types.CallbackQuery, state: FSMContext):
    card_idx = parse_idx(callback.data)
    if card_idx is None:
        await callback.answer("Ошибка: неверный ID карточки.", show_alert=True)
        return

    uid = callback.from_user.id

    # Проверяем, была ли карточка уже открыта
    progress_str = await db.get_day_progress(uid, 2)
    progress = json.loads(progress_str) if isinstance(progress_str, str) else progress_str
    opened_cards = progress.get("cards_opened", [])

    if card_idx in opened_cards:
        await callback.answer("Эта карточка уже была открыта.", show_alert=True)
        return

    await db.mark_card_opened(uid, 2, card_idx)
    await db.update_points(uid, 3)
    
    card = texts.DAY2_CARDS[card_idx]
    card_text = (
        f"<b>{card['title']}</b>\n"
        f"<i>{card['quote']}</i>\n\n"
        f"{card['compliment']}\n"
        f"{card['task']}"
    )
    
    # Определяем путь к изображению в зависимости от индекса
    if card_idx == 0:
        photo_path = "img/Мотивационная карточка.png"
    else:
        photo_path = f"img/Мотивационная карточка-{card_idx}.png"

    try:
        await callback.message.answer_photo(
            photo=types.FSInputFile(photo_path),
            caption=card_text,
            reply_markup=keyboards.day2_after_card_kb()
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить фото {photo_path}: {e}. Отправляю текстом.")
        await callback.message.answer(card_text, reply_markup=keyboards.day2_after_card_kb())

    await callback.message.answer("✅ Отлично! <b>+3 балла</b> добавлены в твой профиль.")
    await callback.answer()


@router.callback_query(F.data == "day2:back_to_cards")
async def back_to_cards(callback: types.CallbackQuery, state: FSMContext):
    await safe_delete_message(callback.message)
    # We might need to delete the text message as well
    try:
        await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id -1)
    except:
        pass
    await start_day2(callback.message, state)
    await callback.answer()

@router.callback_query(Day2States.CHOOSE_CARD, F.data == "day2:opened")
async def handle_day2_opened_card(callback: types.CallbackQuery):
    await callback.answer("Эта карточка уже открыта.", show_alert=True)

@router.callback_query(F.data == "day2:empathy_test")
async def empathy_test(callback: types.CallbackQuery):
    await callback.message.answer(texts.EMPATHY_TEST_TEXT, reply_markup=keyboards.empathy_test_kb())
    await callback.answer()
