from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Document
from typing import List


def doc_list_keyboard(docs: List[Document], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for d in docs[:10]:
        type_emoji = {
            "incoming": "📥",
            "outgoing": "📤",
            "storage": "📦",
            "issued": "📋"
        }.get(d.doc_type, "📄")
        label = f"{type_emoji} #{d.id} {d.name[:20]}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"doc:{d.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"doc_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"doc_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="doc_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def doc_action_keyboard(doc_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "active":
        buttons.append([InlineKeyboardButton(text="✅ Отметить возврат", callback_data=f"doc_return:{doc_id}")])
    buttons.append([InlineKeyboardButton(text="📷 Фото", callback_data=f"doc_photo:{doc_id}")])
    buttons.append([InlineKeyboardButton(text="📋 История", callback_data=f"doc_history:{doc_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="doc_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def doc_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новый документ")],
            [KeyboardButton(text="📋 Входящие")],
            [KeyboardButton(text="📋 Исходящие")],
            [KeyboardButton(text="📋 На хранении")],
            [KeyboardButton(text="📋 Выданные")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
