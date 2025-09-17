import json
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import db
import texts
import keyboards
from states import Day2States
from utils import safe_delete_message # Импортируем из общего хендлера

router = Router()

def parse_idx(cb_data: str) -> int | None:
    if ":" not in cb_data: return None
    _, num = cb_data.split(":", 1)
    return int(num) if num.isdigit() else None
    
# ===== ДЕНЬ 2: КАРТОЧКИ =====

async def start_day2(message: types.Message, state: FSMContext):
    progress_str = await db.get_day_progress(message.from_user.id, 2)
    progress = json.loads(progress_str) if isinstance(progress_str, str) else progress_str

    if len(progress.get("cards_opened", [])) >= 5:
        await message.answer_photo(
            photo=types.FSInputFile("img/Мотивационная карточка-5.png"),
            caption=texts.DAY2_ALL_CARDS_OPENED,
            reply_markup=keyboards.back_to_menu_inline()
        )
        # Отмечаем день пройденным, если еще не отмечен
        if not await db.has_completed_day(message.from_user.id, 2):
            await db.mark_day_completed(message.from_user.id, 2)
        return

    await state.set_state(Day2States.CHOOSE_CARD)
    await db.add_result(message.from_user.id, "Мотивационная карточка дня")

    opened_cards = progress.get("cards_opened", [])
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
    uid = callback.from_user.id
    
    await db.update_points(uid, 3)
    await db.mark_card_opened(uid, 2, card_idx)
    
    card = texts.DAY2_CARDS[card_idx]
    card_text = (
        f"<b>{card['title']}</b>\n"
        f"<i>{card['quote']}</i>\n\n"
        f"{card['compliment']}\n"
        f"{card['task']}"
    )
    
    if card_idx == 0:
        photo_path = "img/Мотивационная карточка.png"
    else:
        photo_path = f"img/Мотивационная карточка-{card_idx}.png"

    await callback.message.answer_photo(
        photo=types.FSInputFile(photo_path),
        caption=card_text
    )
    await callback.message.answer("✅ Отлично! <b>+3 балла</b> добавлены в твой профиль.")
    
    await safe_delete_message(callback.message)
    await start_day2(callback.message, state) # Перезапускаем, чтобы обновить клавиатуру
    await callback.answer()

@router.callback_query(Day2States.CHOOSE_CARD, F.data == "day2:opened")
async def handle_day2_opened_card(callback: types.CallbackQuery):
    await callback.answer("Эта карточка уже открыта.", show_alert=True)