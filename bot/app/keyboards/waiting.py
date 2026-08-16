from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def waiting_time_keyboard(task_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for hours in [1, 2, 3, 4, 6, 12, 24]:
        buttons.append([InlineKeyboardButton(
            text=f"{hours} ч.",
            callback_data=f"wait_time:{task_id}:{hours}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task:{task_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
