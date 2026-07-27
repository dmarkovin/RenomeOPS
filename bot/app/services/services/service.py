from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.database import AsyncSessionLocal
from app.database.models import Service, ServiceOrder, Task, TaskStatus, TaskHistory, TaskPhoto, User, Team
from app.services.tasks.service import create_task
from datetime import datetime

async def create_service(
    name: str,
    description: str,
    price: float,
    category: str = None
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

async def update_service(
    service_id: int,
    name: str = None,
    description: str = None,
    price: float = None,
    category: str = None,
    active: bool = None
) -> Optional[Service]:
    async with AsyncSessionLocal() as db:
        service = await db.get(Service, service_id)
        if not service:
            return None
        if name is not None:
            service.name = name
        if description is not None:
            service.description = description
        if price is not None:
            service.price = price
        if category is not None:
            service.category = category
        if active is not None:
            service.active = active
        await db.commit()
        await db.refresh(service)
        return service

async def get_all_services(active_only: bool = True) -> List[Service]:
    async with AsyncSessionLocal() as db:
        query = select(Service)
        if active_only:
            query = query.where(Service.active == True)
        query = query.order_by(Service.category, Service.name)
        result = await db.execute(query)
        return result.scalars().all()

async def get_service(service_id: int) -> Optional[Service]:
    async with AsyncSessionLocal() as db:
        return await db.get(Service, service_id)

# ==========================
# Заказы услуг с созданием задачи
# ==========================
async def create_service_order(
    service_id: int,
    user_id: int,
    object_data: Dict[str, Any],
    applicant_type: str = None,
    applicant_name: str = None,
    applicant_phone: str = None,
    assigned_to: int = None,
    assigned_team: Team = None,
    comment: str = "",
    photo_ids: List[str] = None
) -> ServiceOrder:
    async with AsyncSessionLocal() as db:
        service = await db.get(Service, service_id)
        if not service:
            raise ValueError("Услуга не найдена")

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
        await db.flush()

        # Создаём задачу
        task = await create_task(
            title=f"Услуга: {service.name}",
            description=f"Заказ #{order.id}: {service.name}\nКомментарий: {comment or '—'}",
            created_by=user_id,
            building=object_data.get("building"),
            entrance=object_data.get("entrance"),
            floor=object_data.get("floor"),
            apartment=object_data.get("apartment"),
            location_type="service",
            parking_level=object_data.get("parking_floor"),
            parking_spot=object_data.get("parking_spot"),
            cellar=object_data.get("cellar"),
            applicant_type=applicant_type or "resident",
            applicant_name=applicant_name or "Заказ услуги",
            applicant_phone=applicant_phone or "",
            priority=3,
            photo_ids=photo_ids or [],
            is_paid=True,
            service_order_id=order.id,
            assigned_to=assigned_to,
            assigned_team=assigned_team
        )

        await db.commit()
        await db.refresh(order)
        return order

async def get_user_orders(user_id: int) -> List[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        query = select(ServiceOrder).where(ServiceOrder.user_id == user_id).order_by(ServiceOrder.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

async def get_all_orders(limit: int = 100, offset: int = 0) -> List[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        query = select(ServiceOrder).order_by(ServiceOrder.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

async def update_order_status(order_id: int, status: str) -> Optional[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        order = await db.get(ServiceOrder, order_id)
        if not order:
            return None
        order.status = status
        order.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(order)
        return order

async def get_order(order_id: int) -> Optional[ServiceOrder]:
    async with AsyncSessionLocal() as db:
        return await db.get(ServiceOrder, order_id)
