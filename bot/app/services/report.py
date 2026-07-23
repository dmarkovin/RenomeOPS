from app.database import get_db



async def get_concierge_report():

    pool = await get_db()


    async with pool.acquire() as conn:


        tasks_total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM tasks
            """
        )


        tasks_done = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status='DONE'
            """
        )


        tasks_work = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status!='DONE'
            """
        )


        deliveries = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM deliveries
            """
        )


        keys = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM keys
            """
        )


        documents = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM documents
            """
        )


        return {

            "tasks_total": tasks_total,

            "tasks_done": tasks_done,

            "tasks_work": tasks_work,

            "deliveries": deliveries,

            "keys": keys,

            "documents": documents

        }
