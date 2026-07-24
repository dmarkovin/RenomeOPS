from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def technician_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="📋 Мои задачи"
                )
            ],

            [
                KeyboardButton(
                    text="📷 Фотоотчет"
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
