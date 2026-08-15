from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Team
from typing import List

def employee_selection_keyboard(employees: List, task_id: int, prefix: str = "task_assign_user_confirm") -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {emp.full_name} ({emp.role.value})",
                callback_data=f"{prefix}:{task_id}:{emp.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def team_selection_keyboard(teams: List, task_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for team_data in teams:
        team = team_data["team"]
        members = team_data["members"]
        buttons.append([
            InlineKeyboardButton(
                text=f"👥 {team.value} ({members} чел.)",
                callback_data=f"task_assign_team_confirm:{task_id}:{team.value}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def assign_type_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Команде", callback_data=f"task_assign_team:{task_id}")],
        [InlineKeyboardButton(text="👤 Сотруднику", callback_data=f"task_assign_user:{task_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")],
    ])

def service_team_selection_keyboard(teams: List) -> InlineKeyboardMarkup:
    buttons = []
    for team_data in teams:
        team = team_data["team"]
        members = team_data["members"]
        buttons.append([
            InlineKeyboardButton(
                text=f"👥 {team.value} ({members} чел.)",
                callback_data=f"service_team:{team.value}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="service_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_employee_selection_keyboard(employees: List) -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {emp.full_name} ({emp.role.value})",
                callback_data=f"service_emp:{emp.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="service_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
