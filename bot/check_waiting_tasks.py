import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.database.models import Task, TaskStatus
from app.services.employees.service import get_employee
from app.services.notification_service import set_bot, notify_admins
from app.config import settings
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def check_waiting_tasks():
    bot = Bot(token=settings.BOT_TOKEN)
    set_bot(bot)
    now = datetime.now()  # Используем локальное время (МСК)
    async with AsyncSessionLocal() as db:
        stmt = select(Task).where(
            and_(
                Task.status == TaskStatus.WAITING,
                Task.wait_until <= now
            )
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        for task in tasks:
            # Если есть исполнитель – уведомляем его
            if task.assigned_to:
                employee = await get_employee(task.assigned_to)
                if employee and employee.telegram_id:
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="▶ Вернуть в работу", callback_data=f"task_status:{task.id}:start")]
                        ]
                    )
                    try:
                        await bot.send_message(
                            employee.telegram_id,
                            f"⏰ Напоминание: задача #{task.id} «{task.title}» была отложена и срок ожидания истёк.\nВерните её в работу или уточните статус.",
                            reply_markup=keyboard
                        )
                    except Exception as e:
                        print(f"Ошибка отправки уведомления для задачи {task.id}: {e}")
            else:
                # Если исполнитель не назначен – уведомляем администраторов
                await notify_admins(
                    f"⏰ Задача #{task.id} «{task.title}» была отложена, но не назначена исполнитель.\n"
                    f"Срок ожидания истёк. Требуется назначение.",
                    notification_type="notify_admin"
                )
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_waiting_tasks())
