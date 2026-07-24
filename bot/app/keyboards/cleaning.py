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
                    text="✅ Выполненные"
                )
            ],

            [
                KeyboardButton(
                    text="📝 Отчет работы"
                )
            ],

            [
                KeyboardButton(
                    text="👤 Профиль"
                )
            ],

            [
                KeyboardButton(
                    text="⬅️ Назад"
                )
            ]

        ],

        resize_keyboard=True

    )

