from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def teams_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="🔧 TEAM_TECH"
                )
            ],

            [
                KeyboardButton(
                    text="🧹 TEAM_CLEANING"
                )
            ],

            [
                KeyboardButton(
                    text="🛡 TEAM_SECURITY"
                )
            ]

        ],
        resize_keyboard=True
    )
