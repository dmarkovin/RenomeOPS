from app.database import get_db


# ===========================================
# Добавить файл
# ===========================================

async def add_file(

    task_id: int,

    telegram_file_id: str,

    uploaded_by: int

):

    pool = await get_db()

    async with pool.acquire() as conn:

        await conn.execute(

            """
            INSERT INTO task_files

            (

                task_id,

                telegram_file_id,

                uploaded_by

            )

            VALUES

            ($1,$2,$3)

            """,

            task_id,

            telegram_file_id,

            uploaded_by

        )


# ===========================================
# Получить все файлы заявки
# ===========================================

async def get_files(

    task_id: int

):

    pool = await get_db()

    async with pool.acquire() as conn:

        return await conn.fetch(

            """
            SELECT *

            FROM task_files

            WHERE task_id=$1

            ORDER BY created_at
            """,

            task_id

        )

