from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, or_, cast, String
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.database.models import Pass, User, Team


async def create_pass(
    type: str,
    guest_name: str = None,
    car_number: str = None,
    purpose: str = None,
    apartment: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None,
    assigned_to: int = None,
    assigned_team: str = None
) -> Pass:
    if start_date is None:
        start_date = datetime.utcnow()
    if end_date is None:
        end_date = start_date.replace(hour=23, minute=59)
    async with AsyncSessionLocal() as db:
        p = Pass(
            type=type,
            guest_name=guest_name,
            car_number=car_number,
            purpose=purpose,
            apartment=apartment,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            photo_ids=photo_ids or [],
            created_by=created_by,
            assigned_to=assigned_to,
            assigned_team=assigned_team,
            status="active"
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        return await db.get(Pass, pass_id)


async def get_passes(
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    status__in: List[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        query = select(Pass).order_by(Pass.created_at.desc())
        if assigned_to:
            query = query.where(Pass.assigned_to == assigned_to)
        if status:
            query = query.where(Pass.status == status)
        if status__in:
            query = query.where(Pass.status.in_(status__in))
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def update_pass_status(pass_id: int, status: str) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return None
        p.status = status
        p.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(p)
        return p


async def check_in(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "active":
            return None
        p.status = "used"
        p.checked_in_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(p)
        return p


async def check_out(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "used":
            return None
        p.checked_out_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass_history(pass_id: int) -> List[dict]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return []
        history = []
        if p.created_at:
            history.append({
                "created_at": p.created_at.strftime('%d.%m.%Y %H:%M'),
                "action": "Создан",
                "user_id": p.created_by,
                "description": f"Тип: {p.type}, {p.guest_name or p.car_number or '—'}"
            })
        if p.checked_in_at:
            history.append({
                "created_at": p.checked_in_at.strftime('%d.%m.%Y %H:%M'),
                "action": "Въезд",
                "user_id": None,
                "description": "Отмечен въезд"
            })
        if p.checked_out_at:
            history.append({
                "created_at": p.checked_out_at.strftime('%d.%m.%Y %H:%M'),
                "action": "Выезд",
                "user_id": None,
                "description": "Отмечен выезд"
            })
        if p.status == "expired":
            history.append({
                "created_at": p.updated_at.strftime('%d.%m.%Y %H:%M'),
                "action": "Закрыт",
                "user_id": None,
                "description": "Пропуск закрыт"
            })
        if p.status == "completed":
            history.append({
                "created_at": p.updated_at.strftime('%d.%m.%Y %H:%M'),
                "action": "Выполнен",
                "user_id": None,
                "description": "Пропуск выполнен"
            })
        return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)


async def search_passes(query: str, limit: int = 20) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        if query.isdigit():
            p = await db.get(Pass, int(query))
            if p:
                return [p]
        stmt = select(Pass).where(
            or_(
                Pass.guest_name.ilike(f"%{query}%"),
                Pass.car_number.ilike(f"%{query}%"),
                cast(Pass.apartment, String).ilike(f"%{query}%")
            )
        ).order_by(Pass.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
