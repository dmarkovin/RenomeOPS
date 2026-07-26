from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def employee_list_keyboard(
    employees: List,
    page: int,
    total_pages: int,
    filters: dict = None,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для списка сотрудников с пагинацией.
    Каждый сотрудник — кнопка с переходом к карточке.
    """
    buttons = []
    for emp in employees:
        status = "✅" if emp.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {emp.full_name} (ID: {emp.id})",
                callback_data=f"emp_card:{emp.id}"
            )
        ])

    # Пагинация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"emp_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"emp_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка поиска / фильтры (можно добавить позже)
    buttons.append([
        InlineKeyboardButton("🔍 Поиск", callback_data="emp_search"),
        InlineKeyboardButton("⬅️ Назад", callback_data="emp_back"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def employee_card_keyboard(user_id: int, active: bool) -> InlineKeyboardMarkup:
    """Клавиатура для карточки сотрудника"""
    buttons = []
    if active:
        buttons.append(InlineKeyboardButton("🚫 Заблокировать", callback_data=f"emp_block:{user_id}"))
    else:
        buttons.append(InlineKeyboardButton("♻️ Активировать", callback_data=f"emp_activate:{user_id}"))
    buttons.append(InlineKeyboardButton("🗑 Удалить", callback_data=f"emp_delete:{user_id}"))
    buttons.append(InlineKeyboardButton("⬅️ Назад к списку", callback_data="emp_back"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
