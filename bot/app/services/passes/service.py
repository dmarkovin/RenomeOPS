from datetime import datetime
from typing import List, Optional, Union
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.database.models import Pass, User, UserRole
from app.services.employees.service import get_employee_by_id


async def create_pass(
    type: str,
    guest_name: Optional[str],
    car_number: Optional[str],
    apartment: Optional[int],
    purpose: Optional[str],
    start_date: datetime,
    end_date: datetime,
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None,
    assigned_to: int = None,
    assigned_team: str = None,
) -> Pass:
    async with AsyncSessionLocal() as db:
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
        )
        db.add(p)
        creator_name = "Система"
        if created_by:
            creator = await get_employee_by_id(created_by)
            if creator:
                creator_name = creator.full_name
        p.history.append({
            "action": "CREATED",
            "user_name": creator_name,
            "details": f"Пропуск создан пользователем {creator_name}",
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass(pass_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Pass)
            .where(Pass.id == pass_id)
            .options(selectinload(Pass.creator), selectinload(Pass.assignee))
        )
        return result.scalar_one_or_none()


async def get_passes(
    status: Optional[Union[str, List[str]]] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        query = select(Pass).options(selectinload(Pass.creator), selectinload(Pass.assignee))
        if status:
            if isinstance(status, list):
                query = query.where(Pass.status.in_(status))
            else:
                query = query.where(Pass.status == status)
        query = query.order_by(Pass.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def search_passes(query: str, limit: int = 20, status: str = None) -> List[Pass]:
    async with AsyncSessionLocal() as db:
        stmt = select(Pass).options(selectinload(Pass.creator), selectinload(Pass.assignee))
        if status:
            stmt = stmt.where(Pass.status == status)
        # Если запрос начинается с #, ищем по ID
        if query.startswith('#'):
            try:
                pass_id = int(query[1:])
                stmt = stmt.where(Pass.id == pass_id)
            except ValueError:
                pass
        elif query.isdigit():
            # Ищем по квартире или ID
            stmt = stmt.where(
                or_(
                    Pass.apartment == int(query),
                    Pass.id == int(query)
                )
            )
        else:
            stmt = stmt.where(
                or_(
                    Pass.guest_name.ilike(f"%{query}%"),
                    Pass.car_number.ilike(f"%{query}%"),
                    Pass.purpose.ilike(f"%{query}%"),
                )
            )
        stmt = stmt.order_by(Pass.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


async def update_pass_status(pass_id: int, status: str, user_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return None
        old_status = p.status
        p.status = status
        p.updated_at = datetime.utcnow()
        user_name = "Система"
        user = await get_employee_by_id(user_id)
        if user:
            user_name = user.full_name
        p.history.append({
            "action": "STATUS_CHANGE",
            "user_name": user_name,
            "details": f"Статус изменён с {old_status} на {status}",
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        await db.refresh(p)
        return p


async def check_in(pass_id: int, user_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status != "active":
            return None
        p.checked_in_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        user_name = "Система"
        user = await get_employee_by_id(user_id)
        if user:
            user_name = user.full_name
        p.history.append({
            "action": "CHECK_IN",
            "user_name": user_name,
            "details": f"Въезд отмечен пользователем {user_name}",
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        await db.refresh(p)
        return p


async def check_out(pass_id: int, user_id: int) -> Optional[Pass]:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p or p.status not in ("active", "used"):
            return None
        p.checked_out_at = datetime.utcnow()
        p.status = "used"
        p.updated_at = datetime.utcnow()
        user_name = "Система"
        user = await get_employee_by_id(user_id)
        if user:
            user_name = user.full_name
        p.history.append({
            "action": "CHECK_OUT",
            "user_name": user_name,
            "details": f"Выезд отмечен пользователем {user_name}",
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        await db.refresh(p)
        return p


async def get_pass_history(pass_id: int) -> List[dict]:
    p = await get_pass(pass_id)
    if not p:
        return []
    return p.history or []


async def add_pass_comment(pass_id: int, user_id: int, user_name: str, text: str) -> bool:
    async with AsyncSessionLocal() as db:
        p = await db.get(Pass, pass_id)
        if not p:
            return False
        if not isinstance(p.comments, list):
            p.comments = []
        p.comments.append({
            "author_id": user_id,
            "author_name": user_name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        })
        p.updated_at = datetime.utcnow()
        p.history.append({
            "action": "COMMENT",
            "user_name": user_name,
            "details": f"Добавлен комментарий: {text[:50]}...",
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        return True


async def count_passes_by_status(status: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Pass).where(Pass.status == status)
        )
        return result.scalar()
