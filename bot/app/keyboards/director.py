from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def director_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="💳 Платные услуги"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
