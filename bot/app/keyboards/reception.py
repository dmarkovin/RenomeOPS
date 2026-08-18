from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def reception_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Новая посылка")],
            [KeyboardButton(text="📋 Список посылок")],
            [KeyboardButton(text="📦 Архив доставки")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def delivery_action_keyboard(delivery_id: int, status: str, user_role: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "pending" and user_role in ("CONCIERGE", "ADMIN"):
        buttons.append([InlineKeyboardButton(text="📥 Выдано", callback_data=f"delivery_receive:{delivery_id}")])
    elif status == "received" and user_role in ("CONCIERGE", "ADMIN"):
        buttons.append([InlineKeyboardButton(text="✅ Завершить", callback_data=f"delivery_complete:{delivery_id}")])
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарии", callback_data=f"delivery_comment_menu:{delivery_id}"),
        InlineKeyboardButton(text="📜 История", callback_data=f"delivery_history:{delivery_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="delivery_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
