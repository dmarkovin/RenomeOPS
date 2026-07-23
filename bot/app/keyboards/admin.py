from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Сотрудники"),
                KeyboardButton(text="🏢 Объект")
            ],
            [
                KeyboardButton(text="📋 Все заявки"),
                KeyboardButton(text="📊 Отчеты")
            ],
            [
                KeyboardButton(text="📜 История действий"),
                KeyboardButton(text="🔎 Поиск")
            ]
        ],
        resize_keyboard=True
    )
