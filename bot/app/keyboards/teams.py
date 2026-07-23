from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def teams_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🔧 Техника"
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
            ],

            [
                KeyboardButton(
                    text="❌ Отмена"
                )
            ]

        ],

        resize_keyboard=True

    )
