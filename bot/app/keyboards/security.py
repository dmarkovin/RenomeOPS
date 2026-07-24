from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def security_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="📋 Мои задачи"
                )
            ],

            [
                KeyboardButton(
                    text="🚨 Инциденты"
                ),
                KeyboardButton(
                    text="📝 Отчет"
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
