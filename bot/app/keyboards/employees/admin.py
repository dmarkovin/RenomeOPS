from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def employees_admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Список сотрудников"),
                KeyboardButton(text="➕ Новый сотрудник"),
            ],
            [
                KeyboardButton(text="📦 Архив сотрудников"),
                KeyboardButton(text="🔍 Поиск"),
            ],
            [
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True
    )
