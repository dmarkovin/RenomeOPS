from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Document
from typing import List

def document_list_keyboard(docs: List[Document], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for d in docs[:10]:
        emoji = "📥" if d.doc_type == "incoming" else "📤" if d.doc_type == "outgoing" else "📦" if d.doc_type == "storage" else "📋"
        label = f"{emoji} #{d.id} {d.title[:20]}"
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

def document_action_keyboard(doc_id: int, doc_type: str, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if doc_type == "issued" and status == "active":
        buttons.append([InlineKeyboardButton(text="✅ Вернуть", callback_data=f"doc_return:{doc_id}")])
    if status != "archived":
        buttons.append([InlineKeyboardButton(text="📦 В архив", callback_data=f"doc_archive:{doc_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="doc_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def document_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Входящий")],
            [KeyboardButton(text="➕ Исходящий")],
            [KeyboardButton(text="📦 На хранение")],
            [KeyboardButton(text="📋 Выдать")],
            [KeyboardButton(text="📋 Список документов")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
