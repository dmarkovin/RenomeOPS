from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Team

def team_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for team in Team:
        buttons.append([InlineKeyboardButton(
            text=team.value,
            callback_data=f"emp_set_team:{user_id}:{team.value}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"emp_card:{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
