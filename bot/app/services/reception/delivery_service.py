from datetime import datetime
from typing import List, Optional, Union
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
            comments=[],
            history=[]
        )
        db.add(delivery)
        await db.flush()
        _add_history(delivery, "CREATED", created_by, "Посылка создана")
        await db.commit()
        await db.refresh(delivery)
        return delivery

async def get_delivery(delivery_id: int) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        return await db.get(Delivery, delivery_id)

async def get_all_deliveries(status: Union[str, List[str]] = None, limit: int = 20, offset: int = 0) -> List[Delivery]:
    async with AsyncSessionLocal() as db:
        query = select(Delivery).order_by(Delivery.created_at.desc())
        if status:
            if isinstance(status, list):
                query = query.where(Delivery.status.in_(status))
            else:
                query = query.where(Delivery.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

async def update_delivery_status(delivery_id: int, status: str) -> Optional[Delivery]:
    async with AsyncSessionLocal() as db:
        delivery = await db.get(Delivery, delivery_id)
        if not delivery:
            return None
        old_status = delivery.status
        delivery.status = status
        delivery.updated_at = datetime.now()
        _add_history(delivery, "STATUS_CHANGE", None, f"Статус изменён с {old_status} на {status}")
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
            "created_at": datetime.now().isoformat()
        })
        delivery.updated_at = datetime.now()
        _add_history(delivery, "COMMENT", user_id, f"Добавлен комментарий: {text[:50]}...")
        await db.commit()
        return True

def _add_history(delivery, action: str, user_id: int = None, details: str = ""):
    if delivery.history is None:
        delivery.history = []
    entry = {
        "action": action,
        "user_id": user_id,
        "author": None,
        "details": details,
        "created_at": datetime.now().isoformat()
    }
    delivery.history.append(entry)

async def get_delivery_history(delivery_id: int) -> List[dict]:
    async with AsyncSessionLocal() as db:
        d = await db.get(Delivery, delivery_id)
        if not d:
            return []
        history = d.history or []
        result = []
        for entry in history:
            author = "Система"
            if entry.get("user_id"):
                from app.services.employees.service import get_employee_by_id
                user = await get_employee_by_id(entry["user_id"])
                if user:
                    author = user.full_name
            result.append({
                "created_at": entry.get("created_at", ""),
                "author": author,
                "action": entry.get("action", ""),
                "description": entry.get("details", "")
            })
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)
