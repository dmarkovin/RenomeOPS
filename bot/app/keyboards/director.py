from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def director_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Отчеты"),
                KeyboardButton(text="📈 Аналитика")
            ],
            [
                KeyboardButton(text="🔎 Поиск"),
                KeyboardButton(text="📜 История")
            ]
        ],
        resize_keyboard=True
    )

