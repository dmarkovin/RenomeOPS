from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def cleaning_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="📋 Мои задачи"
                )
            ],

            [
                KeyboardButton(
                    text="📷 Фото"
                ),

                KeyboardButton(
                    text="📊 Отчет"
                )
            ],

            [
                KeyboardButton(
                    text="👤 Профиль"
                )
            ]

        ],

        resize_keyboard=True

    )
