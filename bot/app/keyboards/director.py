from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def director_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="📈 Отчеты"),
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
