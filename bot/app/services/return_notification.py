from aiogram import Bot

from app.config import settings

bot = Bot(token=settings.BOT_TOKEN)


async def notify_task_return(

    telegram_id: int,

    task_id: int,

    comment: str

):

    await bot.send_message(

        telegram_id,

        f"""
↩ Заявка №{task_id}

возвращена в работу.

Комментарий консьержа:

{comment}
"""

    )
