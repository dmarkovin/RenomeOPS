from aiogram import Bot

from app.config import BOT_TOKEN

bot = Bot(BOT_TOKEN)


# =====================================================
# Новая заявка
# =====================================================

async def notify_new_task(

    telegram_id: int,

    task_id: int,

    title: str,

    priority: str

):

    try:

        await bot.send_message(

            telegram_id,

            f"""
🆕 Вам назначена новая заявка

№ {task_id}

🏷 {title}

⚡ Приоритет:

{priority}

Откройте раздел "📋 Заявки"
"""

        )

    except Exception as e:

        print(e)


# =====================================================
# Передача заявки
# =====================================================

async def notify_transfer(

    telegram_id: int,

    task_id: int,

    comment: str

):

    try:

        await bot.send_message(

            telegram_id,

            f"""
↔ Вам передана заявка

№ {task_id}

Комментарий коллеги:

{comment}
"""

        )

    except Exception as e:

        print(e)


# =====================================================
# Возврат директором
# =====================================================

async def notify_return(

    telegram_id: int,

    task_id: int,

    comment: str

):

    try:

        await bot.send_message(

            telegram_id,

            f"""
⚠ Заявка возвращена

№ {task_id}

Причина:

{comment}
"""

        )

    except Exception as e:

        print(e)
