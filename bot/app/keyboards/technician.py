from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def technician_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
            ],
            [
                KeyboardButton(text="👤 Профиль"),
            ],
        ],
        resize_keyboard=True
    )
