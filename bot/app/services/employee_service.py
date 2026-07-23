from app.database import get_db


async def create_employee(
    telegram_id: int,
    username: str | None,
    full_name: str,
    phone: str | None,
    role: str,
    team: str | None = None,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        employee = await conn.fetchrow(
            """
            INSERT INTO employees
            (
                telegram_id,
                username,
                full_name,
                phone,
                role,
                team
            )
            VALUES
            ($1,$2,$3,$4,$5,$6)
            RETURNING *
            """,
            telegram_id,
            username,
            full_name,
            phone,
            role,
            team
        )

        return employee



async def get_employee(telegram_id: int):

    pool = await get_db()

    async with pool.acquire() as conn:

        employee = await conn.fetchrow(
            """
            SELECT *
            FROM employees
            WHERE telegram_id=$1
            """,
            telegram_id
        )

        return employee



async def is_admin(telegram_id: int):

    employee = await get_employee(telegram_id)

    if not employee:
        return False

    return employee["role"] == "SUPER_ADMIN"



async def get_all_employees():

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *
            FROM employees
            ORDER BY created_at DESC
            """
        )
