from app.config import BOT_USERNAME



def generate_invite_link(
    invite_code: str
) -> str:

    return (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start={invite_code}"
    )
