from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Team, UserRole
from typing import List

def assign_type_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Назначить на команду", callback_data="assign_team")],
            [InlineKeyboardButton(text="👤 Назначить на сотрудника", callback_data="assign_employee")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="assign_cancel")]
        ]
    )

def team_selection_keyboard(teams: List[dict], prefix: str = "assign_team") -> InlineKeyboardMarkup:
    buttons = []
    for team_data in teams:
        team = team_data["team"]
        count = team_data.get("members", 0)
        label = f"{team.value} ({count} чел.)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}:{team.value}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="assign_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def employee_selection_keyboard(employees: List, prefix: str = "assign_emp") -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        label = f"{emp.full_name} ({emp.role.value})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}:{emp.id}:0")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="assign_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== Для платных услуг =====
def service_team_selection_keyboard(teams: List[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for team_data in teams:
        team = team_data["team"]
        count = team_data.get("members", 0)
        label = f"{team.value} ({count} чел.)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"service_team:{team.value}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="service_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_employee_selection_keyboard(employees: List) -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        label = f"{emp.full_name} ({emp.role.value})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"service_emp:{emp.id}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="service_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
