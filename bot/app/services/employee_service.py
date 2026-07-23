from app.database import get_db



async def create_employee(
        telegram_id: int,
        username: str,
        full_name: str,
        role: str = "employee"
):

    pool = await get_db()


    async with pool.acquire() as conn:

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
            telegram_id,
            username,
            full_name,
            role
        )



async def get_employee(telegram_id: int):

    pool = await get_db()


    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM employees
            WHERE telegram_id=$1
            """,
            telegram_id
        )
