import secrets
import string


def generate_invite_code():

    chars = string.ascii_uppercase + string.digits

    code = "".join(
        secrets.choice(chars)
        for _ in range(6)
    )

    return f"RNM-{code}"



def generate_invite_link(
    bot_username: str,
    invite_code: str
):

    return (
        f"https://t.me/{bot_username}"
        f"?start={invite_code}"
    )
