from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole

def settings_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🔔 Уведомления")],
        [KeyboardButton(text="📢 Сообщить о проблеме")],
    ]
    if role == UserRole.ADMIN:
        buttons.append([KeyboardButton(text="🔄 Сменить роль")])
    else:
        buttons.append([KeyboardButton(text="🔄 Сменить команду")])
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
