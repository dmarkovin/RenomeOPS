import os
from dotenv import load_dotenv


load_dotenv()



BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)



BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "RenomeOPS_bot"
)



POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "postgres"
)



POSTGRES_PORT = int(
    os.getenv(
        "POSTGRES_PORT",
        5432
    )
)



POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "renome"
)



POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "renome"
)



POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "renome_password"
)



ADMIN_TELEGRAM_ID = int(
    os.getenv(
        "ADMIN_TELEGRAM_ID",
        0
    )
)
