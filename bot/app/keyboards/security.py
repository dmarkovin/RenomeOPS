from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def security_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="🚶 Обходы"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
                KeyboardButton(text="👤 Профиль"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
