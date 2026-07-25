from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from app.config import settings

bot = Bot(token=settings.BOT_TOKEN)


async def notify_task_check(

    telegram_id: int,

    task_id: int,

    title: str

):

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="✔ Проверить",

                    callback_data=f"check_task:{task_id}"

                )

            ]

        ]

    )

    await bot.send_message(

        telegram_id,

        f"""
📋 Исполнитель завершил работу.

Заявка №{task_id}

<b>{title}</b>

Ожидает проверки.
""",

        reply_markup=keyboard

    )
