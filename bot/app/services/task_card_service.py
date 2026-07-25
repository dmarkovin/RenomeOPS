from app.database import database


async def get_task_card(task_id: int):
    query = """
        SELECT
            t.id,
            t.title,
            t.description,
            t.status,
            t.priority,
            t.object_name,
            t.created_at,

            e.full_name AS executor_name,
            c.full_name AS concierge_name

        FROM tasks t

        LEFT JOIN employees e
            ON e.id = t.executor_id

        LEFT JOIN employees c
            ON c.id = t.created_by

        WHERE t.id = $1
    """

    return await database.fetchrow(query, task_id)
