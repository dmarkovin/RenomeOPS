from app.database import get_db


async def add_history(

    task_id: int,

    employee_id: int | None,

    action: str,

    comment: str | None = None,

    photo_file_id: str | None = None,

    media_group_id: str | None = None,

):

    pool = await get_db()

    async with pool.acquire() as conn:

        await conn.execute(

            """
            INSERT INTO task_history

            (

                task_id,

                employee_id,

                action,

                comment,

                photo_file_id,

                media_group_id

            )

            VALUES

            ($1,$2,$3,$4,$5,$6)

            """,

            task_id,

            employee_id,

            action,

            comment,

            photo_file_id,

            media_group_id

        )


async def get_history(

    task_id: int

):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(

            """
            SELECT

                th.*,

                e.full_name

            FROM task_history th

            LEFT JOIN employees e

            ON th.employee_id=e.id

            WHERE task_id=$1

            ORDER BY created_at

            """,

            task_id

        )
