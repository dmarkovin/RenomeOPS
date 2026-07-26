from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


def employee_roles_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👨‍Управляющий"
                )
            ],
            [
                KeyboardButton(
                    text="🛎 Консьерж"
                )
            ],
            [
                KeyboardButton(
                    text="🔧 Техник"
                )
            ],
            [
                KeyboardButton(
                    text="🧹 Клининг"
                )
            ],
            [
                KeyboardButton(
                    text="🛡 Охрана"
                )
            ]
        ],
        resize_keyboard=True
    )



def employee_create_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="❌ Отмена"
                )
            ]
        ],
        resize_keyboard=True
    )
