from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.database.models import (
    Task,
    TaskStatus,
    User
)

from app.services.logs.service import add_log




async def create_task(

    title:str,

    description:str,

    created_by:int,

    building:str,

    apartment:str,

    priority:int=3

):


    async with AsyncSessionLocal() as db:


        task = Task(

            title=title,

            description=description,

            created_by=created_by,

            building=building,

            apartment=apartment,

            priority=priority,

            status=TaskStatus.CREATED

        )


        db.add(task)


        await db.commit()


        await db.refresh(task)



        await add_log(

            user_id=created_by,

            action="TASK_CREATED",

            description=f"Создана заявка #{task.id}",

            task_id=task.id

        )


        return task





async def get_tasks():


    async with AsyncSessionLocal() as db:


        result = await db.execute(

            select(Task)

            .order_by(
                Task.created_at.desc()
            )

        )


        return result.scalars().all()






async def assign_task(

    task_id:int,

    employee_id:int,

    assigned_by:int

):


    async with AsyncSessionLocal() as db:


        task = await db.get(
            Task,
            task_id
        )


        employee = await db.get(
            User,
            employee_id
        )


        if not task or not employee:

            return None



        task.assigned_to = employee.id

        task.status = TaskStatus.ACCEPTED


        await db.commit()



        await add_log(

            user_id=assigned_by,

            action="TASK_ASSIGNED",

            description=
            f"Заявка #{task.id} назначена {employee.full_name}",

            task_id=task.id

        )


        return task






async def change_status(

    task_id:int,

    status:TaskStatus,

    user_id:int

):


    async with AsyncSessionLocal() as db:


        task = await db.get(
            Task,
            task_id
        )


        if not task:

            return None



        task.status=status


        task.updated_at=datetime.utcnow()



        await db.commit()



        await add_log(

            user_id=user_id,

            action="STATUS_CHANGED",

            description=
            f"Статус заявки #{task.id}: {status}",

            task_id=task.id

        )


        return task
