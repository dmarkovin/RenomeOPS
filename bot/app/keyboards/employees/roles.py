from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import UserRole

def role_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for role in UserRole:
        buttons.append([InlineKeyboardButton(
            text=role.value,
            callback_data=f"emp_set_role:{user_id}:{role.value}"
        )])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="emp_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
