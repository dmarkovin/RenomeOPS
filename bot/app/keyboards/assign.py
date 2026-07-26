from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import User, Team
from typing import List


def assign_type_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа назначения: на команду или на сотрудника"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("👥 На команду", callback_data=f"assign_type_team:{task_id}")],
            [InlineKeyboardButton("👤 На сотрудника", callback_data=f"assign_type_user:{task_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")]
        ]
    )


def team_selection_keyboard(teams: List[dict], task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора команды"""
    buttons = []
    for item in teams:
        team = item["team"]
        members = item["members"]
        buttons.append([
            InlineKeyboardButton(
                f"{team.value} ({members} чел.)",
                callback_data=f"assign_team:{team.value}:{task_id}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def employee_selection_keyboard(employees: List[User], action: str, task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора сотрудника"""
    buttons = []
    for emp in employees:
        status_emoji = "✅" if emp.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {emp.full_name} ({emp.role.value})",
                callback_data=f"{action}_emp:{emp.id}:{task_id}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
