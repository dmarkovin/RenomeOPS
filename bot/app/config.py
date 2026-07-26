import os

from dotenv import load_dotenv


load_dotenv()


class Settings:


    BOT_TOKEN = os.getenv(
        "BOT_TOKEN"
    )


    DB_HOST = os.getenv(
        "POSTGRES_HOST",
        "postgres"
    )

    DB_PORT = os.getenv(
        "POSTGRES_PORT",
        "5432"
    )

    DB_NAME = os.getenv(
        "POSTGRES_DB",
        "renome"
    )

    DB_USER = os.getenv(
        "POSTGRES_USER",
        "renome"
    )

    DB_PASS = os.getenv(
        "POSTGRES_PASSWORD",
        "renome_password"
    )


    REDIS_HOST = os.getenv(
        "REDIS_HOST",
        "redis"
    )


    REDIS_PORT = int(
        os.getenv(
            "REDIS_PORT",
            "6379"
        )
    )


    @property
    def DATABASE_URL(self):

        return (
            "postgresql+asyncpg://"
            f"{self.DB_USER}:"
            f"{self.DB_PASS}@"
            f"{self.DB_HOST}:"
            f"{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )



    @property
    def ADMIN_TELEGRAM_ID(self):

        value = os.getenv(
            "ADMIN_TELEGRAM_ID"
        )

        if value:
            return int(value)

        return None



settings = Settings()



BOT_TOKEN = settings.BOT_TOKEN


POSTGRES_HOST = settings.DB_HOST
POSTGRES_PORT = settings.DB_PORT
POSTGRES_DB = settings.DB_NAME
POSTGRES_USER = settings.DB_USER
POSTGRES_PASSWORD = settings.DB_PASS


ADMIN_TELEGRAM_ID = settings.ADMIN_TELEGRAM_ID
