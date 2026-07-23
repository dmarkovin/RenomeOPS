import asyncpg

from app.config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


pool = None


async def connect_db():

    global pool

    pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


    async with pool.acquire() as conn:

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees
            (
                id SERIAL PRIMARY KEY,

                telegram_id BIGINT UNIQUE NOT NULL,

                username TEXT,

                full_name TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'employee',

                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )


async def close_db():

    global pool

    if pool:
        await pool.close()


async def get_db():

    return pool
