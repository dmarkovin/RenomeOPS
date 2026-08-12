from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def security_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="🚗 Пропуска"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
