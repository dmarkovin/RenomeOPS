from sqlalchemy import select, func
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Pass, PassHistory, User, UserRole


async def create_pass(
    type: str,
    guest_name: str = None,
    car_number: str = None,
    purpose: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None,
    assigned_to: int = None,
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
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            photo_ids=photo_ids or [],
            created_by=created_by,
            assigned_to=assigned_to,
            status="active"
        )
        db.add(p)
        await db.flush()
        # Добавляем запись в историю
        history = PassHistory(
            pass_id=p.id,
            action="created",
            user_id=created_by,
            comment=f"Пропуск создан для {guest_name or car_number}"
        )
        db.add(history)
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        return await db.get(Pass, pass_id)


async def get_passes(
    assigned_to: Optional[int] = None,
    created_by: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        query = select(Pass).order_by(Pass.created_at.desc())
        if assigned_to:
            query = query.where(Pass.assigned_to == assigned_to)
        if created_by:
            query = query.where(Pass.created_by == created_by)
        if status:
            query = query.where(Pass.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def update_pass_status(pass_id: int, status: str) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return None
        p.status = status
        if status == "used":
            p.checked_in_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        # Добавляем запись в историю
        history = PassHistory(
            pass_id=pass_id,
            action=f"status_{status}",
            user_id=None,  # можно передать из вызывающей функции
            comment=f"Статус изменён на {status}"
        )
        db.add(history)
        await db.commit()
        await db.refresh(p)
        return p


async def check_in(pass_id: int, user_id: int = None) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "active":
            return None
        p.status = "used"
        p.checked_in_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        history = PassHistory(
            pass_id=pass_id,
            action="checkin",
            user_id=user_id,
            comment="Въезд отмечен"
        )
        db.add(history)
        await db.commit()
        await db.refresh(p)
        return p


async def check_out(pass_id: int, user_id: int = None) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "used":
            return None
        p.checked_out_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        history = PassHistory(
            pass_id=pass_id,
            action="checkout",
            user_id=user_id,
            comment="Выезд отмечен"
        )
        db.add(history)
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass_history(pass_id: int) -> List[PassHistory]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PassHistory)
            .where(PassHistory.pass_id == pass_id)
            .order_by(PassHistory.created_at.desc())
        )
        return result.scalars().all()

async def count_passes_by_status(status: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Pass).where(Pass.status == status)
        )
        return result.scalar()

async def get_pass_history(pass_id: int) -> List[dict]:
    """Получить историю действий по пропуску"""
    async with AsyncSessionLocal() as db:
        # В истории пропусков у нас есть таблица pass_history
        from app.database.models import PassHistory
        result = await db.execute(
            select(PassHistory).where(PassHistory.pass_id == pass_id).order_by(PassHistory.created_at.desc())
        )
        return result.scalars().all()

async def search_passes(query: str, limit: int = 20) -> List[Pass]:
    """Поиск пропусков по ID, имени гостя, номеру авто"""
    async with AsyncSessionLocal() as db:
        if query.isdigit():
            p = await db.get(Pass, int(query))
            if p:
                return [p]
        stmt = select(Pass).where(
            or_(
                Pass.guest_name.ilike(f"%{query}%"),
                Pass.car_number.ilike(f"%{query}%")
            )
        ).order_by(Pass.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
