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
            status="issued",
            comments=[]
        )
        db.add(key)
        await db.commit()
        await db.refresh(key)
        return key

async def get_key(key_id: int) -> Optional[Key]:
    async with AsyncSessionLocal() as db:
        return await db.get(Key, key_id)

async def get_keys(status: str = None, limit: int = 20, offset: int = 0) -> List[Key]:
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

async def add_key_comment(key_id: int, user_id: int, author_name: str, text: str) -> bool:
    async with AsyncSessionLocal() as db:
        key = await db.get(Key, key_id)
        if not key:
            return False
        if key.comments is None:
            key.comments = []
        key.comments.append({
            "author_id": user_id,
            "author_name": author_name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        })
        key.updated_at = datetime.utcnow()
        await db.commit()
        return True

async def get_key_history(key_id: int) -> List[dict]:
    async with AsyncSessionLocal() as db:
        key = await db.get(Key, key_id)
        if not key:
            return []
        history = []
        if key.created_at:
            history.append({
                "created_at": key.created_at.strftime('%d.%m.%Y %H:%M'),
                "author": "Система",
                "action": "Выдан",
                "description": f"Получатель: {key.recipient}"
            })
        if key.returned_at:
            history.append({
                "created_at": key.returned_at.strftime('%d.%m.%Y %H:%M'),
                "author": "Система",
                "action": "Возвращён",
                "description": ""
            })
        if key.comments:
            for c in key.comments:
                history.append({
                    "created_at": c.get("created_at", ""),
                    "author": c.get("author_name", "—"),
                    "action": "Комментарий",
                    "description": c.get("text", "")
                })
        return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
