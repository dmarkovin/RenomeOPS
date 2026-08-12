import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, and_
from bot.app.database.session import async_session
from bot.app.database.models import Task, User
from bot.app.services.notification_service import notify_user
from bot.app.services.employees.service import get_employee_by_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_waiting_tasks():
    async with async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = select(Task).where(
            and_(
                Task.status == 'waiting',
                Task.wait_until <= now
            )
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            if task.assigned_to:
                user = await get_employee_by_id(task.assigned_to)  # исправлено
                if user and user.active and user.telegram_id:
                    await notify_user(
                        user.telegram_id,
                        f"⏰ Напоминание: задача #{task.id} «{task.title}» ожидает выполнения.\n"
                        f"Срок ожидания истёк {task.wait_until.strftime('%d.%m.%Y %H:%M')}.\n"
                        f"Верните задачу в работу или закройте её."
                    )
                    logger.info(f"Уведомление отправлено для задачи {task.id} пользователю {user.telegram_id}")
            else:
                logger.warning(f"Задача {task.id} не назначена, пропускаем")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(check_waiting_tasks())
