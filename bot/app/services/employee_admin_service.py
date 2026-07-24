from app.database import get_db


async def get_employees(
    active_only: bool = False,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        if active_only:

            return await conn.fetch(
                """
                SELECT *

                FROM employees

                WHERE is_active=TRUE

                ORDER BY full_name
                """
            )

        return await conn.fetch(
            """
            SELECT *

            FROM employees

            ORDER BY full_name
            """
        )


async def get_employee_by_id(
    employee_id: int,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *

            FROM employees

            WHERE id=$1
            """,
            employee_id,
        )


async def block_employee(
    employee_id: int,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.execute(
            """
            UPDATE employees

            SET

                is_active=FALSE,

                blocked_at=NOW()

            WHERE id=$1
            """,
            employee_id,
        )


async def unblock_employee(
    employee_id: int,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.execute(
            """
            UPDATE employees

            SET

                is_active=TRUE,

                blocked_at=NULL

            WHERE id=$1
            """,
            employee_id,
        )


async def delete_employee(
    employee_id: int,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.execute(
            """
            DELETE FROM employees

            WHERE id=$1
            """,
            employee_id,
        )


async def update_employee(

    employee_id: int,

    full_name: str,

    phone: str,

    role: str,

    team: str,

):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            UPDATE employees

            SET

                full_name=$2,

                phone=$3,

                role=$4,

                team=$5

            WHERE id=$1

            RETURNING *
            """,
            employee_id,
            full_name,
            phone,
            role,
            team,
        )


async def employee_statistics():

    pool = await get_db()

    async with pool.acquire() as conn:

        total = await conn.fetchval(
            """
            SELECT COUNT(*)

            FROM employees
            """
        )

        active = await conn.fetchval(
            """
            SELECT COUNT(*)

            FROM employees

            WHERE is_active=TRUE
            """
        )

        blocked = await conn.fetchval(
            """
            SELECT COUNT(*)

            FROM employees

            WHERE is_active=FALSE
            """
        )

        return {

            "total": total,

            "active": active,

            "blocked": blocked,

        }
