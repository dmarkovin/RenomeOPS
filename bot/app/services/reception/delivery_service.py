from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.database.models import Delivery
from app.services.employees.service import get_employee_by_id


async def create_delivery(
    recipient: str,
    apartment: Optional[int],
    courier_service: Optional[str],
    comment: str,
    created_by: int,
    photo_ids: List[str] = None,
) -> Delivery:
    async with AsyncSessionLocal() as db:
        d = Delivery(
            recipient=recipient,
            apartment=apartment,
            courier_service=courier_service,
            comment=comment,
            photo_ids=photo_ids or [],
            created_by=created_by,
            status="pending"
        )
        db.add(d)
        # история
        creator_name = "Система"
        if created_by:
            creator = await get_employee_by_id(created_by)
            if creator:
                creator_name = creator.full_name
        d.comments = []
        await db.commit()
        await db.refresh(d)
        return d


async def get_delivery(delivery_id: int) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Delivery)
            .where(Delivery.id == delivery_id)
            .options(selectinload(Delivery.creator))
        )
        return result.scalar_one_or_none()


async def get_all_deliveries(
    status: str = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Delivery]:
    async with AsyncSessionLocal() as db:
        query = select(Delivery).options(selectinload(Delivery.creator))
        if status:
            query = query.where(Delivery.status == status)
        query = query.order_by(Delivery.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def update_delivery_status(delivery_id: int, status: str) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        d = await db.get(Delivery, delivery_id)
        if not d:
            return None
        d.status = status
        d.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(d)
        return d


async def add_delivery_comment(
    delivery_id: int,
    user_id: int,
    user_name: str,
    text: str
) -> bool:
    async with AsyncSessionLocal() as db:
        d = await db.get(Delivery, delivery_id)
        if not d:
            return False
        if not isinstance(d.comments, list):
            d.comments = []
        d.comments.append({
            "author_id": user_id,
            "author_name": user_name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        })
        d.updated_at = datetime.utcnow()
        await db.commit()
        return True


async def get_delivery_history(delivery_id: int) -> List[dict]:
    d = await get_delivery(delivery_id)
    return d.comments or []  # history в доставке хранится в comments (или можно отдельно)
