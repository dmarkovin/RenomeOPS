from app.database import get_db


async def create_task(
    title: str,
    description: str,
    created_by: int,
    object_id: int | None = None,
    category: str | None = None,
    location: str | None = None,
    priority: str = "NORMAL",
    deadline=None,
):

    pool = await get_db()

    async with pool.acquire() as conn:

        task = await conn.fetchrow(
            """
            INSERT INTO tasks
            (
                title,
                description,
                created_by,
                object_id,
                category,
                location,
                priority,
                deadline
            )

            VALUES
            ($1,$2,$3,$4,$5,$6,$7,$8)

            RETURNING *
            """,
            title,
            description,
            created_by,
            object_id,
            category,
            location,
            priority,
            deadline
        )

        return task


async def get_task(task_id: int):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM tasks
            WHERE id=$1
            """,
            task_id
        )


async def get_all_tasks():

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *
            FROM tasks
            ORDER BY created_at DESC
            """
        )


async def get_open_tasks():

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *
            FROM tasks

            WHERE status IN
            (
                'NEW',
                'ASSIGNED',
                'IN_PROGRESS'
            )

            ORDER BY created_at DESC
            """
        )


async def get_tasks_by_executor(employee_id: int):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *

            FROM tasks

            WHERE assigned_to=$1

            ORDER BY created_at DESC
            """,
            employee_id
        )


async def assign_task(
    task_id: int,
    employee_id: int
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            UPDATE tasks

            SET

                assigned_to=$2,
                status='ASSIGNED'

            WHERE id=$1

            RETURNING *
            """,
            task_id,
            employee_id
        )


async def update_status(
    task_id: int,
    status: str
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            UPDATE tasks

            SET status=$2

            WHERE id=$1

            RETURNING *
            """,
            task_id,
            status
        )


async def complete_task(
    task_id: int,
    comment: str | None = None
):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            UPDATE tasks

            SET

                status='DONE',
                completed_at=NOW(),
                result_comment=$2

            WHERE id=$1

            RETURNING *
            """,
            task_id,
            comment
        )
