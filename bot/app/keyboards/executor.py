from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def executor_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📥 Новые задачи")
            ],
            [
                KeyboardButton(text="🚧 Активные задачи")
            ],
            [
                KeyboardButton(text="👤 Мои задачи")
            ]
        ],
        resize_keyboard=True
    )
