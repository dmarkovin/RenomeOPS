from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def security_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Мои заявки"),
                KeyboardButton(text="📦 Архив"),
            ],
            [
                KeyboardButton(text="👤 Профиль"),
            ],
        ],
        resize_keyboard=True
    )
