from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def employee_list_keyboard(
    employees: List,
    page: int,
    total_pages: int,
    filters: dict = None,
) -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        status = "✅" if emp.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {emp.full_name} (ID: {emp.id})",
                callback_data=f"emp_card:{emp.id}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"emp_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"emp_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(text="🔍 Поиск", callback_data="emp_search"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="emp_back"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def employee_card_keyboard(user_id: int, active: bool) -> InlineKeyboardMarkup:
    """Клавиатура для карточки сотрудника"""
    buttons = []
    if active:
        buttons.append(InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"emp_block:{user_id}"))
    else:
        buttons.append(InlineKeyboardButton(text="♻️ Активировать", callback_data=f"emp_activate:{user_id}"))
    buttons.append(InlineKeyboardButton(text="🔄 Сменить роль", callback_data=f"emp_change_role:{user_id}"))
    buttons.append(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"emp_delete:{user_id}"))
    buttons.append(InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="emp_back"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
