from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import User, Team
from typing import List


def assign_type_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 На команду", callback_data=f"assign_type_team:{task_id}")],
            [InlineKeyboardButton(text="👤 На сотрудника", callback_data=f"assign_type_user:{task_id}")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data=f"assign_skip:{task_id}")]
        ]
    )


def team_selection_keyboard(teams: List[dict], task_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for item in teams:
        team = item["team"]
        members = item["members"]
        label = f"{team.value} ({members} чел.)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"assign_team:{team.value}:{task_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"assign_back_to_type:{task_id}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"assign_skip:{task_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def employee_selection_keyboard(employees: List[User], action: str, task_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        status_emoji = "✅" if emp.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {emp.full_name} ({emp.role.value})",
                callback_data=f"{action}_emp:{emp.id}:{task_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"assign_back_to_type:{task_id}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"assign_skip:{task_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
