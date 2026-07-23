from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def roles_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🛎 Консьерж"
                )
            ],
            [
                KeyboardButton(
                    text="👨‍💼 Директор"
                )
            ],
            [
                KeyboardButton(
                    text="🔧 Исполнитель"
                )
            ],
            [
                KeyboardButton(
                    text="❌ Отмена"
                )
            ]
        ],
        resize_keyboard=True
    )
