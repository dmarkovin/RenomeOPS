from app.database import database


async def add_history(

    task_id: int,

    action: str,

    comment: str = None,

    employee_id: int = None

):

    await database.execute(
        """
        INSERT INTO task_history (

            task_id,

            employee_id,

            action,

            comment

        )

        VALUES (

            $1,

            $2,

            $3,

            $4

        )
        """,

        task_id,

        employee_id,

        action,

        comment

    )


async def get_history(task_id: int):

    return await database.fetch(
        """
        SELECT

            h.created_at,

            h.action,

            h.comment,

            e.full_name

        FROM task_history h

        LEFT JOIN employees e

            ON e.id = h.employee_id

        WHERE h.task_id = $1

        ORDER BY h.created_at DESC
        """,

        task_id

    )
