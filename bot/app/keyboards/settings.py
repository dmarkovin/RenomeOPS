from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole

def settings_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🔔 Уведомления")],
        [KeyboardButton(text="📢 Сообщить о проблеме")],
        [KeyboardButton(text="🔄 Сменить команду")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
