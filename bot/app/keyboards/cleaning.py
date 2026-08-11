from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def cleaning_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Мои задачи"),
                KeyboardButton(text="📦 Архив"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
