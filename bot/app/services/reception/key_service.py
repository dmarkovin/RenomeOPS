from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Key


async def create_key(
    key_number: str,
    recipient: str,
    purpose: str = "",
    comment: str = "",
    created_by: int = None
) -> Key:
    async with AsyncSessionLocal() as db:
        key = Key(
            key_number=key_number,
            recipient=recipient,
            purpose=purpose,
            comment=comment,
            created_by=created_by,
            status="issued"
        )
        db.add(key)
        await db.commit()
        await db.refresh(key)
        return key


async def get_key(key_id: int) -> Optional[Key]:
    async with AsyncSessionLocal() as db:
        return await db.get(Key, key_id)


async def get_keys(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Key]:
    async with AsyncSessionLocal() as db:
        query = select(Key).order_by(Key.created_at.desc())
        if status:
            query = query.where(Key.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def return_key(key_id: int) -> Optional[Key]:
    async with AsyncSessionLocal() as db:
        key = await db.get(Key, key_id)
        if not key or key.status == "returned":
            return None
        key.status = "returned"
        key.returned_at = datetime.utcnow()
        key.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(key)
        return key
