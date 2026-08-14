from datetime import datetime

from sqlalchemy import insert

from app.database import AsyncSessionLocal
from app.database.models import TaskHistory


async def add_log(
    user_id: int,
    action: str,
    description: str,
    task_id: int | None = None,
):

    async with AsyncSessionLocal() as db:

        log = TaskHistory(

            task_id=task_id,

            user_id=user_id,

            action=action,

            description=description,

            created_at=datetime.now()

        )

        db.add(log)

        await db.commit()

        return log
