import secrets
import string

def generate_invite_code(length: int = 8) -> str:
    """Генерация кода приглашения (RNM-XXXXXX)"""
    alphabet = string.ascii_uppercase + string.digits
    return 'RNM-' + ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_invite_link(invite_code: str) -> str:
    """Генерация ссылки для приглашения"""
    # Замените RenomeOPS_bot на имя вашего бота
    return f"https://t.me/RenomeOPS_bot?start={invite_code}"
