from aiogram import Bot

from app.config import settings


bot = Bot(
    token=settings.BOT_TOKEN
)


async def notify_new_task(

    telegram_id: int,

    task_id: int,

    title: str,

    priority: str

):

    from aiogram.types import InlineKeyboardMarkup
    from aiogram.types import InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="📋 Открыть заявку",

                    callback_data=f"task_card:{task_id}"

                )

            ]

        ]

    )

    text = f"""
🔔 <b>Вам назначена новая заявка</b>

№ {task_id}

<b>{title}</b>

Приоритет:

{priority}
"""

    await bot.send_message(

        telegram_id,

        text,

        reply_markup=keyboard

    )
