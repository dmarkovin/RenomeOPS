from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Delivery
from typing import List

def delivery_list_keyboard(deliveries: List[Delivery], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for d in deliveries[:10]:
        status_emoji = "🟡" if d.status == "pending" else "🔵" if d.status == "received" else "✅"
        buttons.append([InlineKeyboardButton(
            f"{status_emoji} #{d.id} {d.recipient[:20]}",
            callback_data=f"delivery:{d.id}"
        )])
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"delivery_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"delivery_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="delivery_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def delivery_action_keyboard(delivery_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "pending":
        buttons.append([InlineKeyboardButton("✅ Получено", callback_data=f"delivery_receive:{delivery_id}")])
    elif status == "received":
        buttons.append([InlineKeyboardButton("✅ Завершить", callback_data=f"delivery_complete:{delivery_id}")])
    buttons.append([InlineKeyboardButton("📷 Фото", callback_data=f"delivery_photo:{delivery_id}")])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="delivery_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
