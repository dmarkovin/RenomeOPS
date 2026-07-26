from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal

from app.database.models import (
    Task,
    TaskStatus,
    TaskHistory,
    User,
)


# ==========================
# Создание заявки
# ==========================

async def create_task(
    title: str,
    description: str,
    created_by: int,
    building: str,
    apartment: str,
    priority: int = 3,
):

    async with AsyncSessionLocal() as db:

        task = Task(
            title=title,
            description=description,
            created_by=created_by,
            building=building,
            apartment=apartment,
            priority=priority,
            status=TaskStatus.CREATED,
        )

        db.add(task)

        await db.commit()

        await db.refresh(task)

        return task



# ==========================
# Получить заявку
# ==========================

async def get_task(task_id: int):

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Task)
            .where(Task.id == task_id)
        )

        return result.scalar_one_or_none()



# ==========================
# Все открытые заявки
# ==========================

async def get_open_tasks():

    async with AsyncSessionLocal() as db:

        result = await db.execute(

            select(Task)
            .where(
                Task.status != TaskStatus.CLOSED
            )
            .order_by(
                Task.created_at.desc()
            )

        )

        return result.scalars().all()



# ==========================
# Мои заявки
# ==========================

async def get_tasks_for_employee(
    user_id: int
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(

            select(Task)
            .where(
                Task.assigned_to == user_id
            )
            .order_by(
                Task.created_at.desc()
            )

        )

        return result.scalars().all()



# ==========================
# Назначить исполнителя
# ==========================

async def assign_task(
    task_id: int,
    employee_id: int,
):

    async with AsyncSessionLocal() as db:


        result = await db.execute(

            select(Task)
            .where(
                Task.id == task_id
            )

        )

        task = result.scalar_one_or_none()


        if task is None:
            return None



        employee = await db.get(
            User,
            employee_id
        )


        if employee is None:
            return None



        task.assigned_to = employee.id

        task.assigned_team = employee.team

        task.status = TaskStatus.ACCEPTED

        task.updated_at = datetime.utcnow()



        db.add(

            TaskHistory(

                task_id=task.id,

                user_id=employee.id,

                action="ASSIGNED",

                description=
                f"Назначен {employee.full_name}",

            )

        )


        await db.commit()


        return task



# ==========================
# Смена статуса
# ==========================

async def change_status(
    task_id: int,
    status: TaskStatus,
    user_id: int,
):

    async with AsyncSessionLocal() as db:


        result = await db.execute(

            select(Task)
            .where(
                Task.id == task_id
            )

        )


        task = result.scalar_one_or_none()


        if task is None:
            return None



        task.status = status

        task.updated_at = datetime.utcnow()



        if status == TaskStatus.CLOSED:

            task.closed_at = datetime.utcnow()



        db.add(

            TaskHistory(

                task_id=task.id,

                user_id=user_id,

                action=status.value.upper(),

                description=
                f"Статус → {status.value}",

            )

        )


        await db.commit()


        return task



# ==========================
# История заявки
# ==========================

async def get_history(
    task_id: int
):

    async with AsyncSessionLocal() as db:


        result = await db.execute(

            select(TaskHistory)

            .where(
                TaskHistory.task_id == task_id
            )

            .order_by(
                TaskHistory.created_at.desc()
            )

        )


        return result.scalars().all()
