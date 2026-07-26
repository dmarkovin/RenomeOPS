from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.database.models import User, UserRole
from app.config import settings


async def create_first_admin():

    if not settings.ADMIN_TELEGRAM_ID:
        return


    async with AsyncSessionLocal() as db:


        result = await db.execute(
            select(User)
            .where(
                User.telegram_id ==
                settings.ADMIN_TELEGRAM_ID
            )
        )


        admin = result.scalar_one_or_none()


        if admin:
            return


        admin = User(

            telegram_id=settings.ADMIN_TELEGRAM_ID,

            username="admin",

            full_name="Главный администратор",

            role=UserRole.ADMIN,

            invite_code="ADMIN",

            active=True,

        )


        db.add(admin)

        await db.commit()


        print(
            "SUPER ADMIN CREATED"
        )
