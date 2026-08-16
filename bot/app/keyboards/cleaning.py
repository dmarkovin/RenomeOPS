from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def cleaning_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
