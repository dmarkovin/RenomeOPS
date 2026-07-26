from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional

from app.database import AsyncSessionLocal
from app.database.models import User, UserRole, Team
from app.utils.invite import generate_invite_code


async def get_employee(telegram_id: int) -> Optional[User]:
    """Получить сотрудника по telegram_id"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_employee_by_id(user_id: int) -> Optional[User]:
    """Получить сотрудника по ID"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_employee_by_invite(invite_code: str) -> Optional[User]:
    """Найти сотрудника по инвайт-коду"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.invite_code == invite_code)
        )
        return result.scalar_one_or_none()


async def activate_employee(user_id: int, telegram_id: int, username: str) -> Optional[User]:
    """Активировать сотрудника (зарегистрировать)"""
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if user:
            user.telegram_id = telegram_id
            user.username = username
            user.active = True
            user.registered_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
        return user


async def create_employee(
    full_name: str,
    phone: str,
    role: UserRole,
    team: Optional[Team] = None,
) -> User:
    """
    Создать нового сотрудника (неактивного, без Telegram ID).
    Генерирует invite_code.
    """
    invite_code = generate_invite_code()
    async with AsyncSessionLocal() as db:
        user = User(
            full_name=full_name,
            phone=phone,
            role=role,
            team=team,
            invite_code=invite_code,
            active=False,
            telegram_id=None,
            username=None,
            registered_at=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def get_all_employees(
    active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    team: Optional[Team] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[User]:
    """
    Получить список сотрудников с фильтрацией и пагинацией.
    """
    async with AsyncSessionLocal() as db:
        query = select(User)
        filters = []
        if active is not None:
            filters.append(User.active == active)
        if role:
            filters.append(User.role == role)
        if team:
            filters.append(User.team == team)
        if search:
            filters.append(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.phone.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                )
            )
        if filters:
            query = query.where(and_(*filters))
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def count_employees(
    active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    team: Optional[Team] = None,
    search: Optional[str] = None,
) -> int:
    """Количество сотрудников для пагинации"""
    async with AsyncSessionLocal() as db:
        query = select(User)
        filters = []
        if active is not None:
            filters.append(User.active == active)
        if role:
            filters.append(User.role == role)
        if team:
            filters.append(User.team == team)
        if search:
            filters.append(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.phone.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                )
            )
        if filters:
            query = query.where(and_(*filters))
        result = await db.execute(query)
        return len(result.scalars().all())


async def block_employee(user_id: int) -> Optional[User]:
    """Заблокировать сотрудника (active=False)"""
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if user:
            user.active = False
            await db.commit()
            await db.refresh(user)
        return user


async def activate_employee_by_admin(user_id: int) -> Optional[User]:
    """Активировать сотрудника вручную (если он уже зарегистрирован)"""
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if user:
            user.active = True
            await db.commit()
            await db.refresh(user)
        return user


async def delete_employee(user_id: int) -> bool:
    """Удалить сотрудника (для администратора)"""
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
            await db.commit()
            return True
        return False
