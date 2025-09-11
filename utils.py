import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
import keyboards
from config import ADMINS

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in ADMINS

async def to_main_menu(message: types.Message, state: FSMContext):
    """Возвращает пользователя в главное меню и сбрасывает состояние."""
    await state.clear()
    await message.answer("Главное меню.", reply_markup=keyboards.main_menu_kb())

async def safe_delete_message(message: types.Message):
    """Безопасно удаляет сообщение, игнорируя возможные ошибки."""
    try:
        await message.delete()
    except Exception as e:
        logging.debug(f"Не удалось удалить сообщение: {e}")

def parse_idx(cb_data: str) -> int | None:
    """Извлекает числовой индекс из данных колбэка (например, 'card:1' -> 1)."""
    if ":" not in cb_data: return None
    try:
        _, num_str = cb_data.split(":", 1)
        return int(num_str)
    except (ValueError, IndexError):
        return None

