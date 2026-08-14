from typing import List, Optional
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.database.models import Service, ServiceOrder, User, Team


async def create_service(
    name: str,
    description: str = None,
    price: float = 0.0,
    category: str = None,
) -> Service:
    async with AsyncSessionLocal() as db:
        service = Service(
            name=name,
            description=description,
            price=price,
            category=category,
            active=True
        )
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service


async def update_service(service_id: int, **kwargs) -> Optional[Service]:
    async with AsyncSessionLocal() as db:
        service = await db.get(Service, service_id)
        if not service:
            return None
        for key, value in kwargs.items():
            if hasattr(service, key):
                setattr(service, key, value)
        await db.commit()
        await db.refresh(service)
        return service


async def delete_service(service_id: int) -> bool:
    """Деактивирует услугу (мягкое удаление)"""
    async with AsyncSessionLocal() as db:
        service = await db.get(Service, service_id)
        if not service:
            return False
        service.active = False
        await db.commit()
        return True


async def get_all_services(active_only: bool = True, limit: int = 100, offset: int = 0) -> List[Service]:
    async with AsyncSessionLocal() as db:
        query = select(Service).order_by(Service.created_at.desc())
        if active_only:
            query = query.where(Service.active == True)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()


async def get_service(service_id: int) -> Optional[Service]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()


async def create_service_order(
    service_id: int,
    user_id: int,
    object_data: dict,
    applicant_type: str = None,
    applicant_name: str = None,
    applicant_phone: str = None,
    assigned_to: int = None,
    assigned_team: Team = None,
    comment: str = "",
    photo_ids: List[str] = None,
) -> ServiceOrder:
    async with AsyncSessionLocal() as db:
        order = ServiceOrder(
            service_id=service_id,
            user_id=user_id,
            building=object_data.get("building"),
            entrance=object_data.get("entrance"),
            floor=object_data.get("floor"),
            apartment=object_data.get("apartment"),
            parking_floor=object_data.get("parking_floor"),
            parking_spot=object_data.get("parking_spot"),
            cellar=object_data.get("cellar"),
            comment=comment,
            photo_ids=photo_ids or [],
            status="pending"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order


async def get_user_orders(user_id: int) -> List[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ServiceOrder).where(ServiceOrder.user_id == user_id).order_by(ServiceOrder.created_at.desc())
        )
        return result.scalars().all()


async def get_all_orders(limit: int = 100, offset: int = 0) -> List[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ServiceOrder).order_by(ServiceOrder.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()


async def update_order_status(order_id: int, status: str) -> Optional[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        order = await db.get(ServiceOrder, order_id)
        if not order:
            return None
        order.status = status
        order.updated_at = datetime.now()
        await db.commit()
        await db.refresh(order)
        return order


async def get_order(order_id: int) -> Optional[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        return await db.get(ServiceOrder, order_id)
