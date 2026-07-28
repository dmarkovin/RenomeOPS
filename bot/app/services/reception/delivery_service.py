from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Delivery

async def create_delivery(
    recipient: str,
    apartment: int = None,
    courier_service: str = None,
    comment: str = "",
    created_by: int = None,
    photo_ids: List[str] = None
) -> Delivery:
    async with AsyncSessionLocal() as db:
        delivery = Delivery(
            recipient=recipient,
            apartment=apartment,
            courier_service=courier_service or "",
            comment=comment,
            created_by=created_by,
            photo_ids=photo_ids or [],
            status="pending",
            comments=[]
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery

async def get_delivery(delivery_id: int) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        return await db.get(Delivery, delivery_id)

async def get_all_deliveries(status: str = None, limit: int = 20, offset: int = 0) -> List[Delivery]:
    async with AsyncSessionLocal() as db:
        query = select(Delivery).order_by(Delivery.created_at.desc())
        if status:
            query = query.where(Delivery.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

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

async def add_delivery_comment(delivery_id: int, user_id: int, author_name: str, text: str) -> bool:
    async with AsyncSessionLocal() as db:
        delivery = await db.get(Delivery, delivery_id)
        if not delivery:
            return False
        if delivery.comments is None:
            delivery.comments = []
        delivery.comments.append({
            "author_id": user_id,
            "author_name": author_name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        })
        delivery.updated_at = datetime.utcnow()
        await db.commit()
        return True

async def get_delivery_history(delivery_id: int) -> List[dict]:
    async with AsyncSessionLocal() as db:
        delivery = await db.get(Delivery, delivery_id)
        if not delivery:
            return []
        history = []
        if delivery.created_at:
            history.append({
                "created_at": delivery.created_at.strftime('%d.%m.%Y %H:%M'),
                "author": "Система",
                "action": "Создана",
                "description": f"Получатель: {delivery.recipient}"
            })
        if delivery.status == "received" or delivery.status == "completed":
            history.append({
                "created_at": delivery.updated_at.strftime('%d.%m.%Y %H:%M') if delivery.updated_at else delivery.created_at.strftime('%d.%m.%Y %H:%M'),
                "author": "Система",
                "action": f"Статус изменён на {delivery.status}",
                "description": ""
            })
        if delivery.comments:
            for c in delivery.comments:
                history.append({
                    "created_at": c.get("created_at", ""),
                    "author": c.get("author_name", "—"),
                    "action": "Комментарий",
                    "description": c.get("text", "")
                })
        return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
