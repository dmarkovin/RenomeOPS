from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Key
from typing import List

def key_list_keyboard(keys: List[Key], page: int, total_pages: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    for k in keys[:10]:
        status_emoji = "🔑" if k.status == "issued" else "✅"
        label = f"{status_emoji} #{k.id} {k.key_number} – {k.recipient}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"key:{k.id}")])
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"key_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"key_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="key_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
