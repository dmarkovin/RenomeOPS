from sqlalchemy import select

from app.config import ADMIN_TELEGRAM_ID
from app.database import AsyncSessionLocal

from app.database.models import User


async def create_first_admin():

    if not ADMIN_TELEGRAM_ID:
        return


    async with AsyncSessionLocal() as db:


        result = await db.execute(
            select(User)
            .where(
                User.telegram_id == ADMIN_TELEGRAM_ID
            )
        )


        exists = result.scalar_one_or_none()


        if exists:
            return



        admin = User(

            telegram_id=ADMIN_TELEGRAM_ID,

            username="admin",

            full_name="Главный администратор",

            role="SUPER_ADMIN",

            active=True,

        )


        db.add(admin)


        await db.commit()


        print(
            "First SUPER_ADMIN created"
        )
