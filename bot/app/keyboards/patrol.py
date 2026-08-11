from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Patrol
from typing import List

def patrol_list_keyboard(patrols: List[Patrol], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for p in patrols[:10]:
        status_emoji = "🔄" if p.status == "active" else "✅"
        label = f"{status_emoji} #{p.id} {p.route}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"patrol:{p.id}")])
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"patrol_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"patrol_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="patrol_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def patrol_action_keyboard(patrol_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "active":
        buttons.append([InlineKeyboardButton(text="✅ Завершить обход", callback_data=f"patrol_complete:{patrol_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="patrol_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def patrol_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новый обход")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
