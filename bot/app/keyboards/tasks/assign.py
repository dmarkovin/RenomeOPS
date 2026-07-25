from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def assign_keyboard(employees):

    keyboard = []

    for employee in employees:

        keyboard.append(

            [

                InlineKeyboardButton(

                    text=employee["full_name"],

                    callback_data=f"assign_employee:{employee['id']}"

                )

            ]

        )

    keyboard.append(

        [

            InlineKeyboardButton(

                text="❌ Отмена",

                callback_data="assign_cancel"

            )

        ]

    )

    return InlineKeyboardMarkup(

        inline_keyboard=keyboard

    )
