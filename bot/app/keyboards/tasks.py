from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


def task_categories():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🚰 Сантехника"
                ),
                KeyboardButton(
                    text="💡 Электрика"
                )
            ],

            [
                KeyboardButton(
                    text="🧹 Клининг"
                ),
                KeyboardButton(
                    text="🛡 Безопасность"
                )
            ],

            [
                KeyboardButton(
                    text="🏢 Административная"
                ),
                KeyboardButton(
                    text="🔧 Техническая"
                )
            ],

            [
                KeyboardButton(
                    text="📦 Другое"
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


def priority_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🟢 Низкий"
                )
            ],

            [
                KeyboardButton(
                    text="🟡 Обычный"
                )
            ],

            [
                KeyboardButton(
                    text="🟠 Высокий"
                )
            ],

            [
                KeyboardButton(
                    text="🔴 Авария"
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


def confirmation_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="✅ Создать заявку"
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
