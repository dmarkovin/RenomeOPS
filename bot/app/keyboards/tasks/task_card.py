from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def task_card_keyboard(
    role: str,
    status: str,
    task_id: int,
):

    buttons = []

    if role == "CONCIERGE":

        if status == "NEW":

            buttons.append([
                InlineKeyboardButton(
                    text="👤 Назначить",
                    callback_data=f"assign:{task_id}"
                )
            ])

            buttons.append([
                InlineKeyboardButton(
                    text="👥 Открыть команде",
                    callback_data=f"open:{task_id}"
                )
            ])

        if status in [
            "NEW",
            "ASSIGNED",
            "IN_PROGRESS"
        ]:

            buttons.append([
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"cancel:{task_id}"
                )
            ])

    elif role == "DIRECTOR":

        buttons.append([
            InlineKeyboardButton(
                text="👤 Назначить",
                callback_data=f"assign:{task_id}"
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                text="🔄 Переназначить",
                callback_data=f"reassign:{task_id}"
            )
        ])

        if status == "DONE":

            buttons.append([
                InlineKeyboardButton(
                    text="⭐ Оценить",
                    callback_data=f"rate:{task_id}"
                )
            ])

    else:

        if status == "NEW":

            buttons.append([
                InlineKeyboardButton(
                    text="✅ Взять",
                    callback_data=f"take:{task_id}"
                )
            ])

        if status == "ASSIGNED":

            buttons.append([
                InlineKeyboardButton(
                    text="▶ Начать",
                    callback_data=f"start:{task_id}"
                )
            ])

        if status == "IN_PROGRESS":

            buttons.append([
                InlineKeyboardButton(
                    text="⏸ Пауза",
                    callback_data=f"pause:{task_id}"
                )
            ])

            buttons.append([
                InlineKeyboardButton(
                    text="↔ Передать",
                    callback_data=f"transfer:{task_id}"
                )
            ])

            buttons.append([
                InlineKeyboardButton(
                    text="📷 Фото",
                    callback_data=f"photo:{task_id}"
                )
            ])

            buttons.append([
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"finish:{task_id}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="📜 История",
            callback_data=f"history:{task_id}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
