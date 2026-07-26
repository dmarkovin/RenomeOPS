from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def waiting_time_keyboard(task_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="1 час", callback_data=f"wait_time:{task_id}:1")],
        [InlineKeyboardButton(text="2 часа", callback_data=f"wait_time:{task_id}:2")],
        [InlineKeyboardButton(text="4 часа", callback_data=f"wait_time:{task_id}:4")],
        [InlineKeyboardButton(text="8 часов", callback_data=f"wait_time:{task_id}:8")],
        [InlineKeyboardButton(text="24 часа", callback_data=f"wait_time:{task_id}:24")],
        [InlineKeyboardButton(text="48 часов", callback_data=f"wait_time:{task_id}:48")],
        [InlineKeyboardButton(text="72 часа", callback_data=f"wait_time:{task_id}:72")],
        [InlineKeyboardButton(text="Неделя", callback_data=f"wait_time:{task_id}:168")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
