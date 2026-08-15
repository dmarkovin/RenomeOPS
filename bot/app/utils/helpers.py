from aiogram.types import CallbackQuery
from app.config import settings

BOT_ID = 8892179840  # ID вашего бота

def get_user_id_from_callback(callback: CallbackQuery) -> int:
    """
    Возвращает реальный ID пользователя из callback.
    Если from_user.id равен ID бота, используем chat.id.
    """
    user_id = callback.from_user.id
    if user_id == BOT_ID:
        # Если ID бота, берём ID чата
        user_id = callback.message.chat.id
    return user_id
