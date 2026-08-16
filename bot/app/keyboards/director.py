from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def director_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
                KeyboardButton(text="📦 Доставка"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
