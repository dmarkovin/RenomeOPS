from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def employees_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Добавить сотрудника"
                )
            ],
            [
                KeyboardButton(
                    text="📋 Список сотрудников"
                )
            ],
            [
                KeyboardButton(
                    text="🚫 Заблокировать сотрудника"
                )
            ],
            [
                KeyboardButton(
                    text="🗑 Удалить сотрудника"
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
