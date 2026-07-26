from .task_list import task_list_keyboard, get_task_status_emoji
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole

def tasks_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        buttons = [
            [KeyboardButton(text="➕ Создать заявку")],
            [KeyboardButton(text="📋 Список заявок")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
