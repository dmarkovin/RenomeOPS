from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def date_selection_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    action: 'start' или 'end'
    """
    today = datetime.now().date()
    buttons = [
        [InlineKeyboardButton(text="📅 Сегодня", callback_data=f"date_{action}:{today.strftime('%Y-%m-%d')}")],
        [InlineKeyboardButton(text="📅 Завтра", callback_data=f"date_{action}:{(today + timedelta(days=1)).strftime('%Y-%m-%d')}")],
        [InlineKeyboardButton(text="📅 Через 3 дня", callback_data=f"date_{action}:{(today + timedelta(days=3)).strftime('%Y-%m-%d')}")],
        [InlineKeyboardButton(text="📅 Через 7 дней", callback_data=f"date_{action}:{(today + timedelta(days=7)).strftime('%Y-%m-%d')}")],
        [InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"date_{action}_manual")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
