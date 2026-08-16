from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def concierge_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="Пропуска"),
            ],
            [
                KeyboardButton(text="Доставка"),
                KeyboardButton(text="Документы"),
            ],
            [
                KeyboardButton(text="Ключи"),
                KeyboardButton(text="Платные услуги"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
