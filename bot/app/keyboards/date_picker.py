from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def date_selection_keyboard(prefix: str, days_offset: int = 0) -> InlineKeyboardMarkup:
    """
    prefix: 'start' или 'end'
    days_offset: сдвиг от текущей даты (0 — сегодня, 1 — завтра и т.д.)
    """
    buttons = []
    today = datetime.now().date()
    for i in range(days_offset, days_offset + 7):
        date = today + timedelta(days=i)
        label = date.strftime("%d.%m")
        callback = f"date_{prefix}:{date.strftime('%Y-%m-%d')}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=callback)])
    buttons.append([InlineKeyboardButton(text="📅 Ввести вручную", callback_data=f"date_{prefix}_manual")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="date_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
