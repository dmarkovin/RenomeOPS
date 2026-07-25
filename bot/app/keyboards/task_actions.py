from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def task_actions_keyboard(task_id: int):

    return InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👤 Назначить",
                    callback_data=f"assign:{task_id}"
                ),

                InlineKeyboardButton(
                    text="↔ Передать",
                    callback_data=f"transfer:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💬 Комментарии",
                    callback_data=f"comments:{task_id}"
                ),

                InlineKeyboardButton(
                    text="📷 Фото",
                    callback_data=f"photos:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📜 История",
                    callback_data=f"history:{task_id}"
                ),

                InlineKeyboardButton(
                    text="⚠ Приоритет",
                    callback_data=f"priority:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🕒 Дедлайн",
                    callback_data=f"deadline:{task_id}"
                ),

                InlineKeyboardButton(
                    text="🏢 Объект",
                    callback_data=f"object:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Закрыть",
                    callback_data=f"close:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="tasks"
                )
            ]

        ]

    )
