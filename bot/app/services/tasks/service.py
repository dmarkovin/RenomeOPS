from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func, cast, String
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.database.models import (
    Task,
    TaskStatus,
    TaskHistory,
    TaskPhoto,
    Comment,
    User,
    UserRole,
    Team,
)
from app.metrics import tasks_created_total, tasks_closed_total


# ==========================
# Допустимые переходы статусов
# ==========================
STATUS_TRANSITIONS = {
    'created': ['accepted', 'waiting', 'paused', 'closed'],
    'waiting': ['accepted', 'paused', 'closed'],
    'accepted': ['in_progress', 'paused', 'closed'],
    'in_progress': ['checking', 'paused', 'closed'],
    'checking': ['closed', 'in_progress'],
    'paused': ['in_progress', 'accepted', 'closed'],
    'closed': [],
}

def can_transition(old_status: str, new_status: str) -> bool:
    return new_status in STATUS_TRANSITIONS.get(old_status, [])


# ==========================
# Создание заявки (единственная версия)
# ==========================
async def create_task(
    title: str,
    description: str,
    created_by: int,
    building: int = None,
    entrance: int = None,
    floor: int = None,
    apartment: int = None,
    location_type: str = None,
    parking_level: int = None,
    parking_spot: int = None,
    cellar: int = None,
    applicant_type: str = None,
    applicant_name: str = None,
    applicant_phone: str = None,
    priority: int = 3,
    photo_ids: List[str] = None,
    is_paid: bool = False,
    is_feedback: bool = False,
    is_role_change: bool = False,
    service_order_id: int = None,
    assigned_to: int = None,
    assigned_team: Team = None
) -> Task:
    async with AsyncSessionLocal() as db:
        task = Task(
            title=title,
            description=description,
            created_by=created_by,
            building=building,
            entrance=entrance,
            floor=floor,
            apartment=apartment,
            location_type=location_type,
            parking_level=parking_level,
            parking_spot=parking_spot,
            cellar=cellar,
            applicant_type=applicant_type,
            applicant_name=applicant_name,
            applicant_phone=applicant_phone,
            priority=priority,
            is_paid=is_paid,
            is_feedback=is_feedback,
            is_role_change=is_role_change,
            service_order_id=service_order_id,
            assigned_to=assigned_to,
            assigned_team=assigned_team,
            status="created"
        )
        db.add(task)
        await db.flush()

        if photo_ids:
            for file_id in photo_ids:
                photo = TaskPhoto(
                    task_id=task.id,
                    telegram_file_id=file_id,
                    uploaded_by=created_by,
                )
                db.add(photo)

        history = TaskHistory(
            task_id=task.id,
            user_id=created_by,
            action="CREATED",
            description=f"Задача создана: {title}" + (" (платная)" if is_paid else "") + (" (обращение)" if is_feedback else "") + (" (смена роли)" if is_role_change else ""),
        )
        db.add(history)
        await db.commit()
        await db.refresh(task)
        tasks_created_total.inc()
        return task


# ==========================
# Получить заявку с подгрузкой
# ==========================
async def get_task(task_id: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.creator),
                selectinload(Task.assignee),
                selectinload(Task.comments).selectinload(Comment.author),
                selectinload(Task.photos),
                selectinload(Task.history).selectinload(TaskHistory.user),
            )
        )
        return result.scalar_one_or_none()


# ==========================
# Списки заявок
# ==========================
async def get_open_tasks(limit: int = 20, offset: int = 0, user_id: int = None) -> List[Task]:
    async with AsyncSessionLocal() as db:
        query = select(Task).where(cast(Task.status, String) != "closed")
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role != UserRole.ADMIN:
                query = query.where(Task.is_feedback == False)
        query = query.order_by(Task.priority.desc(), Task.created_at.desc())
        query = query.limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def get_tasks_for_employee(
    user_id: int,
    status: str = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Task]:
    async with AsyncSessionLocal() as db:
        employee = await db.get(User, user_id)
        if not employee:
            return []

        query = select(Task).where(
            or_(
                Task.assigned_to == user_id,
                cast(Task.assigned_team, String) == employee.team.value,
            )
        )
        if employee.role != UserRole.ADMIN:
            query = query.where(Task.is_feedback == False)
        if employee.role != UserRole.ADMIN:
            query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        if status:
            query = query.where(cast(Task.status, String) == status)
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_open_tasks() -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(cast(Task.status, String) != "closed")
        )
        return result.scalar()


async def count_tasks_for_employee(user_id: int, status: str = None) -> int:
    async with AsyncSessionLocal() as db:
        employee = await db.get(User, user_id)
        if not employee:
            return 0
        query = select(func.count()).select_from(Task).where(
            or_(
                Task.assigned_to == user_id,
                cast(Task.assigned_team, String) == employee.team.value,
            )
        )
        if employee.role != UserRole.ADMIN:
            query = query.where(Task.is_feedback == False)
        if employee.role != UserRole.ADMIN:
            query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        if status:
            query = query.where(cast(Task.status, String) == status)
        result = await db.execute(query)
        return result.scalar()


# ==========================
# Назначение на команду
# ==========================
async def assign_task_to_team(task_id: int, team: Team, assigned_by: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            task = await db.get(Task, task_id, with_for_update=True)
            if not task:
                return None
            if task.status not in ('created', 'waiting'):
                return None
            task.assigned_team = team
            task.assigned_to = None
            task.updated_at = datetime.utcnow()
            history = TaskHistory(
                task_id=task.id,
                user_id=assigned_by,
                action="ASSIGNED_TEAM",
                description=f"Задача назначена на команду {team.value}",
            )
            db.add(history)
            await db.commit()
            return task


# ==========================
# Назначение на конкретного сотрудника (с блокировкой и перехватом)
# ==========================
async def assign_task_to_user(task_id: int, user_id: int, assigned_by: int, force: bool = False) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            task = await db.get(Task, task_id, with_for_update=True)
            if not task:
                return None
            if task.status not in ('created', 'waiting'):
                return None
            employee = await db.get(User, user_id)
            if not employee or not employee.active:
                return None
            if not force and task.assigned_team and employee.team != task.assigned_team:
                return None
            task.assigned_to = user_id
            task.assigned_team = employee.team
            if task.status == "created":
                task.status = "accepted"
            task.updated_at = datetime.utcnow()
            history = TaskHistory(
                task_id=task.id,
                user_id=assigned_by,
                action="ASSIGNED_USER",
                description=f"Назначен исполнитель: {employee.full_name}",
            )
            db.add(history)
            await db.commit()
            return task


# ==========================
# Взять задачу (исполнитель из команды) с блокировкой и перехватом
# ==========================
async def take_task(task_id: int, user_id: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            task = await db.get(Task, task_id, with_for_update=True)
            if not task:
                return None
            employee = await db.get(User, user_id)
            if not employee or not employee.active:
                return None
            if task.status in ("closed", "checking"):
                return None
            if task.assigned_to is not None and employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
                return None
            if employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
                if task.assigned_team and employee.team != task.assigned_team:
                    return None
            task.assigned_to = user_id
            if task.status == "created":
                task.status = "accepted"
            task.updated_at = datetime.utcnow()
            history = TaskHistory(
                task_id=task.id,
                user_id=user_id,
                action="TAKEN",
                description=f"Сотрудник {employee.full_name} взял задачу в работу",
            )
            db.add(history)
            await db.commit()
            return task


# ==========================
# Передать задачу другому сотруднику
# ==========================
async def transfer_task(
    task_id: int,
    from_user_id: int,
    to_user_id: int,
    comment: str = None,
) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            task = await db.get(Task, task_id, with_for_update=True)
            if not task:
                return None
            if task.assigned_to != from_user_id:
                return None
            new_assignee = await db.get(User, to_user_id)
            if not new_assignee or not new_assignee.active:
                return None
            old_assignee = await db.get(User, from_user_id)
            old_name = old_assignee.full_name if old_assignee else "неизвестно"
            task.assigned_to = to_user_id
            task.assigned_team = new_assignee.team
            task.updated_at = datetime.utcnow()
            history_text = f"Передано от {old_name} к {new_assignee.full_name}"
            if comment:
                history_text += f"\nКомментарий: {comment}"
            history = TaskHistory(
                task_id=task.id,
                user_id=from_user_id,
                action="TRANSFERRED",
                description=history_text,
            )
            db.add(history)
            await db.commit()
            return task


# ==========================
# Изменить статус (с валидацией перехода)
# ==========================
async def change_status(
    task_id: int,
    new_status: str,
    user_id: int,
    comment: str = None,
    wait_until: datetime = None,
) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            task = await db.get(Task, task_id, with_for_update=True)
            if not task:
                return None
            if not can_transition(task.status, new_status):
                return None
            old_status = task.status
            task.status = new_status
            task.updated_at = datetime.utcnow()
            if new_status == "closed":
                task.closed_at = datetime.utcnow()
                tasks_closed_total.inc()
            if new_status == "waiting" and wait_until:
                task.wait_until = wait_until
            else:
                task.wait_until = None

            action = f"Статус изменён: {old_status} → {new_status}"
            if comment:
                action += f"\nКомментарий: {comment}"
            if wait_until:
                action += f"\nОжидание до: {wait_until.strftime('%d.%m.%Y %H:%M')}"

            history = TaskHistory(
                task_id=task.id,
                user_id=user_id,
                action=f"STATUS_CHANGE_{new_status.upper()}",
                description=action,
            )
            db.add(history)
            await db.commit()
            return task


# ==========================
# Добавить комментарий (убедимся, что сохраняется)
# ==========================
async def add_comment(
    task_id: int,
    user_id: int,
    text: str,
) -> Optional[Comment]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            return None
        comment = Comment(
            task_id=task_id,
            author_id=user_id,
            text=text,
        )
        db.add(comment)
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action="COMMENT",
            description=f"Добавлен комментарий: {text[:50]}...",
        )
        db.add(history)
        await db.commit()
        await db.refresh(comment)
        return comment


# ==========================
# Добавить фото
# ==========================
async def add_photo(
    task_id: int,
    user_id: int,
    file_id: str,
) -> Optional[TaskPhoto]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            return None
        photo = TaskPhoto(
            task_id=task_id,
            telegram_file_id=file_id,
            uploaded_by=user_id,
        )
        db.add(photo)
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action="PHOTO",
            description=f"Добавлено фото (file_id: {file_id[:10]}...)",
        )
        db.add(history)
        await db.commit()
        await db.refresh(photo)
        return photo


# ==========================
# Получить историю задачи
# ==========================
async def get_task_history(task_id: int) -> List[TaskHistory]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .options(selectinload(TaskHistory.user))
        )
        return result.scalars().all()


# ==========================
# Получить список сотрудников и команд для назначения
# ==========================
async def get_available_employees(
    role: Optional[UserRole] = None,
    team: Optional[Team] = None,
    exclude_id: Optional[int] = None,
) -> List[User]:
    async with AsyncSessionLocal() as db:
        query = select(User).where(User.active == True)
        if role:
            query = query.where(User.role == role)
        if team:
            query = query.where(User.team == team)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        query = query.order_by(User.full_name)
        result = await db.execute(query)
        return result.scalars().all()


async def get_teams_with_members() -> List[dict]:
    async with AsyncSessionLocal() as db:
        teams = [Team.TEAM_TECH, Team.TEAM_CLEANING, Team.TEAM_SECURITY, Team.TEAM_CONCIERGE, Team.ADMIN_TEAM, Team.DIRECTOR_TEAM]
        result = []
        for team in teams:
            count_query = select(func.count()).select_from(User).where(
                User.team == team,
                User.active == True
            )
            count = await db.execute(count_query)
            cnt = count.scalar()
            result.append({"team": team, "members": cnt})
        return result


# ==========================
# Архив (закрытые задачи) – с фильтрацией по правам
# ==========================
async def get_tasks_by_status(status: str, limit: int = 20, offset: int = 0, user_id: int = None) -> List[Task]:
    async with AsyncSessionLocal() as db:
        query = select(Task).where(cast(Task.status, String) == status)

        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)

        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_tasks_by_status(status: str, user_id: int = None) -> int:
    async with AsyncSessionLocal() as db:
        query = select(func.count()).select_from(Task).where(cast(Task.status, String) == status)
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        result = await db.execute(query)
        return result.scalar()


async def get_paid_closed_tasks(limit: int = 20, offset: int = 0, user_id: int = None) -> List[Task]:
    async with AsyncSessionLocal() as db:
        query = select(Task).where(
            and_(
                cast(Task.status, String) == "closed",
                Task.is_paid == True
            )
        )
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_paid_closed_tasks(user_id: int = None) -> int:
    async with AsyncSessionLocal() as db:
        query = select(func.count()).select_from(Task).where(
            and_(
                cast(Task.status, String) == "closed",
                Task.is_paid == True
            )
        )
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        result = await db.execute(query)
        return result.scalar()


async def get_regular_closed_tasks(limit: int = 20, offset: int = 0, user_id: int = None) -> List[Task]:
    async with AsyncSessionLocal() as db:
        query = select(Task).where(
            and_(
                cast(Task.status, String) == "closed",
                Task.is_paid == False
            )
        )
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_regular_closed_tasks(user_id: int = None) -> int:
    async with AsyncSessionLocal() as db:
        query = select(func.count()).select_from(Task).where(
            and_(
                cast(Task.status, String) == "closed",
                Task.is_paid == False
            )
        )
        if user_id:
            user = await db.get(User, user_id)
            if user and user.role == UserRole.ADMIN:
                pass
            elif user and user.role in (UserRole.CONCIERGE, UserRole.DIRECTOR):
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
            else:
                query = query.where(
                    or_(
                        Task.assigned_to == user_id,
                        cast(Task.assigned_team, String) == user.team.value
                    )
                )
                query = query.where(Task.is_feedback == False)
                query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        result = await db.execute(query)
        return result.scalar()


async def search_tasks(query: str, limit: int = 20) -> List[Task]:
    async with AsyncSessionLocal() as db:
        if query.isdigit():
            task = await db.get(Task, int(query))
            if task:
                return [task]
        stmt = select(Task).where(
            or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%"),
                Task.assignee.has(User.full_name.ilike(f"%{query}%"))
            )
        ).order_by(Task.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


async def get_checking_tasks(limit: int = 20, offset: int = 0) -> List[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(cast(Task.status, String) == "checking")
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
        )
        return result.scalars().all()


async def count_checking_tasks() -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(cast(Task.status, String) == "checking")
        )
        return result.scalar()


async def get_team_tasks(
    user_id: int,
    status: str = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Task]:
    async with AsyncSessionLocal() as db:
        employee = await db.get(User, user_id)
        if not employee:
            return []
        query = select(Task).where(
            and_(
                cast(Task.assigned_team, String) == employee.team.value,
                Task.assigned_to.is_(None)
            )
        )
        if employee.role != UserRole.ADMIN:
            query = query.where(Task.is_feedback == False)
            query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        if status:
            query = query.where(cast(Task.status, String) == status)
        else:
            query = query.where(cast(Task.status, String) != "closed")
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_team_tasks(user_id: int, status: str = None) -> int:
    async with AsyncSessionLocal() as db:
        employee = await db.get(User, user_id)
        if not employee:
            return 0
        query = select(func.count()).select_from(Task).where(
            and_(
                cast(Task.assigned_team, String) == employee.team.value,
                Task.assigned_to.is_(None)
            )
        )
        if employee.role != UserRole.ADMIN:
            query = query.where(Task.is_feedback == False)
            query = query.where(cast(Task.assigned_team, String) != Team.ADMIN_TEAM.value)
        if status:
            query = query.where(cast(Task.status, String) == status)
        else:
            query = query.where(cast(Task.status, String) != "closed")
        result = await db.execute(query)
        return result.scalar()
