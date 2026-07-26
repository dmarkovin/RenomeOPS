from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def concierge_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="💳 Платные услуги"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
                KeyboardButton(text="🔄 Обходы"),
            ],
            [
                KeyboardButton(text="📦 Посылки"),
                KeyboardButton(text="🗝 Ключи"),
            ],
            [
                KeyboardButton(text="📑 Документы"),
                KeyboardButton(text="📊 Отчеты"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
