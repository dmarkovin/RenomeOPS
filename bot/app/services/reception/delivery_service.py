from sqlalchemy import select
from typing import List, Optional
from app.database import AsyncSessionLocal
from app.database.models import Delivery, User
from datetime import datetime

async def create_delivery(
    recipient: str,
    apartment: int,
    courier_service: str,
    comment: str,
    created_by: int,
    photo_ids: List[str] = None
) -> Delivery:
    async with AsyncSessionLocal() as db:
        delivery = Delivery(
            recipient=recipient,
            apartment=apartment,
            courier_service=courier_service,
            comment=comment,
            created_by=created_by,
            photo_ids=photo_ids or [],
            status="pending"
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery

async def get_all_deliveries(status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Delivery]:
    async with AsyncSessionLocal() as db:
        query = select(Delivery).order_by(Delivery.created_at.desc())
        if status:
            query = query.where(Delivery.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

async def get_delivery(delivery_id: int) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        return await db.get(Delivery, delivery_id)

async def update_delivery_status(delivery_id: int, status: str) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        delivery = await db.get(Delivery, delivery_id)
        if not delivery:
            return None
        delivery.status = status
        delivery.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(delivery)
        return delivery
