from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def concierge_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="💳 Платные услуги"),
            ],
            [
                KeyboardButton(text="📦 Доставка"),
                KeyboardButton(text="🔑 Ключи"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
