from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def priority_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔴 Критический", callback_data="priority:5")],
        [InlineKeyboardButton(text="🟠 Высокий", callback_data="priority:4")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="priority:3")],
        [InlineKeyboardButton(text="🟢 Низкий", callback_data="priority:2")],
        [InlineKeyboardButton(text="⚪ Неважно", callback_data="priority:1")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_priority_name(priority: int) -> str:
    mapping = {
        5: "🔴 Критический",
        4: "🟠 Высокий",
        3: "🟡 Средний",
        2: "🟢 Низкий",
        1: "⚪ Неважно",
    }
    return mapping.get(priority, f"Приоритет {priority}")
