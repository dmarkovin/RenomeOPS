from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Patrol, Task, TaskStatus, User, Team


async def create_patrol(
    route: str,
    notes: str = "",
    photo_ids: List[str] = None,
    video_ids: List[str] = None,
    created_by: int = None,
    task_id: int = None
) -> Patrol:
    async with AsyncSessionLocal() as db:
        patrol = Patrol(
            route=route,
            notes=notes,
            photo_ids=photo_ids or [],
            video_ids=video_ids or [],
            created_by=created_by,
            task_id=task_id,
            status="active"
        )
        db.add(patrol)
        await db.commit()
        await db.refresh(patrol)
        return patrol


async def get_patrol(patrol_id: int) -> Optional[Patrol]:
    async with AsyncSessionLocal() as db:
        return await db.get(Patrol, patrol_id)


async def get_patrols(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Patrol]:
    async with AsyncSessionLocal() as db:
        query = select(Patrol).order_by(Patrol.created_at.desc())
        if user_id:
            query = query.where(Patrol.created_by == user_id)
        if status:
            query = query.where(Patrol.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def complete_patrol(patrol_id: int) -> Optional[Patrol]:
    async with AsyncSessionLocal() as db:
        patrol = await db.get(Patrol, patrol_id)
        if not patrol:
            return None
        patrol.status = "completed"
        patrol.end_time = datetime.utcnow()
        patrol.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(patrol)
        return patrol
