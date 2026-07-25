from app.database import get_db

import random
import string



def generate_invite_code():

    return (
        "RNM-"
        +
        "".join(
            random.choices(
                string.digits,
                k=5
            )
        )
    )



async def create_employee(
    telegram_id: int | None,
    username: str | None,
    full_name: str,
    phone: str | None,
    role: str,
    team: str | None = None,
):

    pool = await get_db()

    invite_code = generate_invite_code()


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
                team,
                invite_code
            )

            VALUES
            ($1,$2,$3,$4,$5,$6,$7)

            RETURNING *
            """,

            telegram_id,
            username,
            full_name,
            phone,
            role,
            team,
            invite_code
        )

        return employee




async def get_employee(
    telegram_id: int
):

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




async def get_employee_by_invite(
    invite_code: str
):

    pool = await get_db()


    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM employees
            WHERE invite_code=$1
            """,

            invite_code
        )




async def activate_employee(
    employee_id: int,
    telegram_id: int,
    username: str | None
):

    pool = await get_db()


    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            UPDATE employees

            SET
                telegram_id=$2,
                username=$3,
                invite_code=NULL

            WHERE id=$1

            RETURNING *
            """,

            employee_id,
            telegram_id,
            username
        )




async def is_admin(
    telegram_id: int
):

    employee = await get_employee(
        telegram_id
    )

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
# =====================================================
# Получить сотрудников команды
# =====================================================

async def get_team_members(team: str):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *

            FROM employees

            WHERE team=$1

            ORDER BY full_name
            """,
            team
        )


# =====================================================
# Получить сотрудника по ID
# =====================================================

async def get_employee_by_id(employee_id: int):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *

            FROM employees

            WHERE id=$1
            """,
            employee_id
        )
