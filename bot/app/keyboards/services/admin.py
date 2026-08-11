from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Service

def service_admin_list_keyboard(services: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        status = "✅" if s.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{s.name} — {s.price} руб. {status}",
                callback_data=f"service_admin_edit:{s.id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"service_admin_delete:{s.id}"
            )
        ])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"service_admin_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"service_admin_page:{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="➕ Создать услугу", callback_data="service_admin_create")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="service_admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_admin_edit_keyboard(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Название", callback_data=f"service_edit_name:{service_id}")],
        [InlineKeyboardButton(text="✏️ Описание", callback_data=f"service_edit_description:{service_id}")],
        [InlineKeyboardButton(text="✏️ Цена", callback_data=f"service_edit_price:{service_id}")],
        [InlineKeyboardButton(text="✏️ Категория", callback_data=f"service_edit_category:{service_id}")],
        [InlineKeyboardButton(text="🔄 Активность", callback_data=f"service_edit_active:{service_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"service_edit_back:{service_id}")],
    ])
