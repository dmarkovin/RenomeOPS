from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
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


# ==========================
# Создание заявки
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
    photo_ids: List[str] = None
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
            status=TaskStatus.CREATED,
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
            description=f"Задача создана: {title}",
        )
        db.add(history)
        await db.commit()
        await db.refresh(task)
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
async def get_open_tasks(limit: int = 20, offset: int = 0) -> List[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(Task.status != TaskStatus.CLOSED)
            .order_by(Task.priority.desc(), Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
        )
        return result.scalars().all()


async def get_tasks_for_employee(
    user_id: int,
    status: Optional[TaskStatus] = None,
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
                Task.assigned_team == employee.team,
            )
        )
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        query = query.options(selectinload(Task.creator), selectinload(Task.assignee))
        result = await db.execute(query)
        return result.scalars().all()


async def count_open_tasks() -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status != TaskStatus.CLOSED)
        )
        return result.scalar()


async def count_tasks_for_employee(user_id: int, status: Optional[TaskStatus] = None) -> int:
    async with AsyncSessionLocal() as db:
        employee = await db.get(User, user_id)
        if not employee:
            return 0
        query = select(func.count()).select_from(Task).where(
            or_(
                Task.assigned_to == user_id,
                Task.assigned_team == employee.team,
            )
        )
        if status:
            query = query.where(Task.status == status)
        result = await db.execute(query)
        return result.scalar()


# ==========================
# Назначение на команду
# ==========================
async def assign_task_to_team(task_id: int, team: Team, assigned_by: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
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
        await db.refresh(task)
        return task


# ==========================
# Назначение на конкретного сотрудника
# ==========================
async def assign_task_to_user(task_id: int, user_id: int, assigned_by: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            return None
        employee = await db.get(User, user_id)
        if not employee:
            return None
        task.assigned_to = user_id
        task.assigned_team = employee.team
        if task.status == TaskStatus.CREATED:
            task.status = TaskStatus.ACCEPTED
        task.updated_at = datetime.utcnow()
        history = TaskHistory(
            task_id=task.id,
            user_id=assigned_by,
            action="ASSIGNED_USER",
            description=f"Назначен исполнитель: {employee.full_name}",
        )
        db.add(history)
        await db.commit()
        await db.refresh(task)
        return task


# ==========================
# Взять задачу (исполнитель из команды)
# ==========================
async def take_task(task_id: int, user_id: int) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            return None
        employee = await db.get(User, user_id)
        if not employee:
            return None
        if task.assigned_team != employee.team or task.assigned_to is not None:
            return None
        task.assigned_to = user_id
        if task.status == TaskStatus.CREATED:
            task.status = TaskStatus.ACCEPTED
        task.updated_at = datetime.utcnow()
        history = TaskHistory(
            task_id=task.id,
            user_id=user_id,
            action="TAKEN",
            description=f"Сотрудник {employee.full_name} взял задачу в работу",
        )
        db.add(history)
        await db.commit()
        await db.refresh(task)
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
        task = await db.get(Task, task_id)
        if not task:
            return None
        if task.assigned_to != from_user_id:
            return None
        new_assignee = await db.get(User, to_user_id)
        if not new_assignee:
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
        await db.refresh(task)
        return task


# ==========================
# Изменить статус
# ==========================
async def change_status(
    task_id: int,
    new_status: TaskStatus,
    user_id: int,
    comment: str = None,
) -> Optional[Task]:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            return None
        old_status = task.status
        task.status = new_status
        task.updated_at = datetime.utcnow()
        if new_status == TaskStatus.CLOSED:
            task.closed_at = datetime.utcnow()
        action = f"Статус изменён: {old_status.value} → {new_status.value}"
        if comment:
            action += f"\nКомментарий: {comment}"
        history = TaskHistory(
            task_id=task.id,
            user_id=user_id,
            action=f"STATUS_CHANGE_{new_status.value.upper()}",
            description=action,
        )
        db.add(history)
        await db.commit()
        await db.refresh(task)
        return task


# ==========================
# Добавить комментарий
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
        teams = [Team.TEAM_TECH, Team.TEAM_CLEANING, Team.TEAM_SECURITY, Team.TEAM_CONCIERGE]
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
# Архив (закрытые задачи)
# ==========================
async def get_tasks_by_status(status: TaskStatus, limit: int = 20, offset: int = 0) -> List[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
        )
        return result.scalars().all()


async def count_tasks_by_status(status: TaskStatus) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status == status)
        )
        return result.scalar()

# ==========================
# Архив (закрытые задачи)
# ==========================
async def get_tasks_by_status(status: TaskStatus, limit: int = 20, offset: int = 0) -> List[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
        )
        return result.scalars().all()

async def count_tasks_by_status(status: TaskStatus) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status == status)
        )
        return result.scalar()

async def get_teams_with_members() -> List[dict]:
    async with AsyncSessionLocal() as db:
        teams = [Team.TEAM_TECH, Team.TEAM_CLEANING, Team.TEAM_SECURITY, Team.TEAM_CONCIERGE]
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
# Архив (закрытые задачи)
# ==========================
async def get_tasks_by_status(status: TaskStatus, limit: int = 20, offset: int = 0) -> List[Task]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
        )
        return result.scalars().all()

async def count_tasks_by_status(status: TaskStatus) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status == status)
        )
        return result.scalar()
