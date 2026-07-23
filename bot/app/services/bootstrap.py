from app.config import ADMIN_TELEGRAM_ID
from app.database import get_db


async def create_first_admin():

    if not ADMIN_TELEGRAM_ID:
        return


    pool = await get_db()


    async with pool.acquire() as conn:

        exists = await conn.fetchrow(
            """
            SELECT *
            FROM employees
            WHERE telegram_id=$1
            """,
            ADMIN_TELEGRAM_ID
        )


        if exists:
            return


        await conn.execute(
            """
            INSERT INTO employees
            (
                telegram_id,
                username,
                full_name,
                role
            )
            VALUES
            ($1,$2,$3,$4)
            """,
            ADMIN_TELEGRAM_ID,
            "admin",
            "Главный администратор",
            "SUPER_ADMIN"
        )

        print(
            "First SUPER_ADMIN created"
        )
