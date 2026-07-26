import secrets
import string

from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.database.models import (
    User,
    UserRole,
    Team,
)


def generate_invite():

    chars = (
        string.ascii_uppercase
        + string.digits
    )

    return (
        "RNM-"
        +
        "".join(
            secrets.choice(chars)
            for _ in range(8)
        )
    )



async def create_employee(
    full_name: str,
    role: UserRole,
    team: Team | None = None,
    phone: str | None = None,
):

    async with AsyncSessionLocal() as db:


        employee = User(

            full_name=full_name,

            phone=phone,

            role=role,

            team=team,

            invite_code=generate_invite(),

            active=False,

        )


        db.add(employee)

        await db.commit()

        await db.refresh(employee)


        return employee



async def get_employee(
    telegram_id:int
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(

            select(User)
            .where(
                User.telegram_id ==
                telegram_id
            )

        )

        return result.scalar_one_or_none()



async def get_employee_by_invite(
    code:str
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(

            select(User)
            .where(
                User.invite_code ==
                code
            )

        )

        return result.scalar_one_or_none()



async def activate_employee(
    user_id:int,
    telegram_id:int,
    username:str|None
):

    async with AsyncSessionLocal() as db:

        user = await db.get(
            User,
            user_id
        )


        if user:

            user.telegram_id = telegram_id

            user.username=username

            user.active=True

            user.registered_at=datetime.utcnow()


            await db.commit()


        return user
