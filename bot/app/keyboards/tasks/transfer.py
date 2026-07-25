from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def transfer_keyboard(employees):

    keyboard = []

    for employee in employees:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=employee["full_name"],
                    callback_data=f"transfer_to:{employee['id']}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="transfer_cancel"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
