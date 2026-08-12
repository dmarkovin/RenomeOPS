from datetime import datetime
from typing import List, Optional, Union
from sqlalchemy import select, or_, cast, String, and_
from app.database import AsyncSessionLocal
from app.database.models import Pass, User, Team


def _add_history(pass_obj, action: str, user_id: int = None, details: str = ""):
    if pass_obj.history is None:
        pass_obj.history = []
    entry = {
        "action": action,
        "user_id": user_id,
        "details": details,
        "created_at": datetime.utcnow().isoformat()
    }
    pass_obj.history.append(entry)


async def create_pass(
    type: str,
    guest_name: str = None,
    car_number: str = None,
    apartment: int = None,
    purpose: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None,
    assigned_to: int = None,
    assigned_team: str = None
) -> Pass:
    async with AsyncSessionLocal() as db:
        if assigned_to:
            user = await db.get(User, assigned_to)
            if not user or not user.active:
                raise ValueError("Назначенный сотрудник не активен")
        p = Pass(
            type=type,
            guest_name=guest_name,
            car_number=car_number,
            apartment=apartment,
            purpose=purpose,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            photo_ids=photo_ids or [],
            created_by=created_by,
            assigned_to=assigned_to,
            assigned_team=assigned_team,
            status="active",
            history=[],
            comments=[]
        )
        db.add(p)
        await db.flush()
        _add_history(p, "CREATED", created_by, f"Создан пропуск типа {type}")
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        return await db.get(Pass, pass_id)


async def get_passes(
    status: Union[str, List[str]] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        query = select(Pass).order_by(Pass.created_at.desc())
        if status:
            if isinstance(status, list):
                query = query.where(Pass.status.in_(status))
            else:
                query = query.where(Pass.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def count_passes_by_status(status: Union[str, List[str]] = None) -> int:
    async with AsyncSessionLocal() as db:
        query = select(Pass)
        if status:
            if isinstance(status, list):
                query = query.where(Pass.status.in_(status))
            else:
                query = query.where(Pass.status == status)
        result = await db.execute(query)
        return len(result.scalars().all())


async def update_pass_status(pass_id: int, status: str, user_id: int = None) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return None
        old_status = p.status
        p.status = status
        p.updated_at = datetime.utcnow()
        _add_history(p, "STATUS_CHANGE", user_id, f"Статус изменён с {old_status} на {status}")
        await db.commit()
        await db.refresh(p)
        return p


async def check_in(pass_id: int, user_id: int = None) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "active":
            return None
        p.checked_in_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        _add_history(p, "CHECK_IN", user_id, "Отмечен въезд")
        await db.commit()
        await db.refresh(p)
        return p


async def check_out(pass_id: int, user_id: int = None) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "active":
            return None
        p.checked_out_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        _add_history(p, "CHECK_OUT", user_id, "Отмечен выезд")
        await db.commit()
        await db.refresh(p)
        return p


async def add_pass_comment(pass_id: int, user_id: int, author_name: str, text: str) -> bool:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return False
        if p.comments is None:
            p.comments = []
        p.comments.append({
            "author_id": user_id,
            "author_name": author_name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        })
        p.updated_at = datetime.utcnow()
        _add_history(p, "COMMENT", user_id, f"Добавлен комментарий: {text[:50]}")
        await db.commit()
        return True


async def get_pass_history(pass_id: int) -> List[dict]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return []
        return p.history or []


async def search_passes(query: str, limit: int = 20, status: str = None) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        like = f"%{query}%"
        conditions = [
            Pass.guest_name.ilike(like),
            Pass.car_number.ilike(like),
            cast(Pass.apartment, String).ilike(like),
            Pass.purpose.ilike(like),
            Pass.comment.ilike(like)
        ]
        if query.startswith("#"):
            try:
                pass_id = int(query[1:])
                stmt = select(Pass).where(Pass.id == pass_id)
                if status:
                    stmt = stmt.where(Pass.status == status)
                result = await db.execute(stmt)
                return result.scalars().all()
            except ValueError:
                return []
        stmt = select(Pass)
        if status:
            stmt = stmt.where(and_(Pass.status == status, or_(*conditions)))
        else:
            stmt = stmt.where(or_(*conditions))
        stmt = stmt.order_by(Pass.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
