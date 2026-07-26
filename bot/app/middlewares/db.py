from aiogram import BaseMiddleware

from app.database.db import AsyncSessionLocal


class DatabaseMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler,
        event,
        data
    ):

        async with AsyncSessionLocal() as session:

            data["session"] = session

            return await handler(
                event,
                data
            )
