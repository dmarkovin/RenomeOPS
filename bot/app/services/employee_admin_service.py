from sqlalchemy import select, update, delete, func

from app.database import AsyncSessionLocal

from app.database.models import User



async def get_employees(
    active_only: bool = False,
):

    async with AsyncSessionLocal() as db:


        query = select(User)


        if active_only:

            query = query.where(
                User.active == True
            )


        query = query.order_by(
            User.full_name
        )


        result = await db.execute(query)


        return result.scalars().all()




async def get_employee_by_id(
    employee_id: int,
):

    async with AsyncSessionLocal() as db:

        return await db.get(
            User,
            employee_id
        )




async def block_employee(
    employee_id: int,
):

    async with AsyncSessionLocal() as db:

        employee = await db.get(
            User,
            employee_id
        )


        if employee:

            employee.active = False

            await db.commit()



        return employee




async def unblock_employee(
    employee_id: int,
):

    async with AsyncSessionLocal() as db:

        employee = await db.get(
            User,
            employee_id
        )


        if employee:

            employee.active = True

            await db.commit()



        return employee




async def delete_employee(
    employee_id: int,
):

    async with AsyncSessionLocal() as db:


        employee = await db.get(
            User,
            employee_id
        )


        if employee:

            await db.delete(employee)

            await db.commit()



        return employee




async def update_employee(

    employee_id: int,

    full_name: str,

    phone: str,

    role: str,

    team: str,

):

    async with AsyncSessionLocal() as db:


        employee = await db.get(
            User,
            employee_id
        )


        if not employee:
            return None



        employee.full_name = full_name

        employee.phone = phone

        employee.role = role

        employee.team = team



        await db.commit()

        await db.refresh(employee)



        return employee




async def employee_statistics():

    async with AsyncSessionLocal() as db:


        total = await db.scalar(

            select(
                func.count(User.id)
            )

        )


        active = await db.scalar(

            select(
                func.count(User.id)
            )
            .where(
                User.active == True
            )

        )


        blocked = await db.scalar(

            select(
                func.count(User.id)
            )
            .where(
                User.active == False
            )

        )


        return {

            "total": total,

            "active": active,

            "blocked": blocked,

        }
