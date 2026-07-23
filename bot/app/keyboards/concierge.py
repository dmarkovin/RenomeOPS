from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def concierge_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки")
            ],
            [
                KeyboardButton(text="💰 Платные услуги"),
                KeyboardButton(text="📦 Доставки")
            ],
            [
                KeyboardButton(text="🔑 Ключи"),
                KeyboardButton(text="📄 Документы")
            ],
            [
                KeyboardButton(text="🚪 Пропуска"),
                KeyboardButton(text="🚶 Обходы")
            ],
            [
                KeyboardButton(text="📝 Заметки"),
                KeyboardButton(text="🔎 Поиск")
            ],
            [
                KeyboardButton(text="📦 Архив")
            ]
        ],
        resize_keyboard=True
    )
