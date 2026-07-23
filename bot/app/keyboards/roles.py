from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def roles_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🏢 Администрация"
                )
            ],

            [
                KeyboardButton(
                    text="🛎 Консьерж Сервис"
                )
            ],

            [
                KeyboardButton(
                    text="🔧 Технический специалист"
                )
            ],

            [
                KeyboardButton(
                    text="🧹 Сотрудник клининга"
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
