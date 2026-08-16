from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def priority_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i in range(1, 6):
        emoji = ["🟢", "🟢", "🟡", "🟠", "🔴"][i-1]
        label = f"{emoji} {i}★"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"priority:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
