from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.database.models import User


async def get_employee(
    telegram_id: int
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User)
            .where(
                User.telegram_id == telegram_id
            )
        )

        return result.scalar_one_or_none()



async def get_employee_by_invite(
    invite_code: str
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User)
            .where(
                User.invite_code == invite_code
            )
        )

        return result.scalar_one_or_none()



async def activate_employee(
    user_id: int,
    telegram_id: int,
    username: str | None
):

    async with AsyncSessionLocal() as db:

        user = await db.get(
            User,
            user_id
        )

        if user:

            user.telegram_id = telegram_id
            user.username = username
            user.active = True

            await db.commit()

            await db.refresh(user)

        return user
