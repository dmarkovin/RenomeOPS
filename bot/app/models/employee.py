from dataclasses import dataclass
from datetime import datetime


@dataclass
class Employee:
    id: int
    telegram_id: int
    username: str | None
    full_name: str
    role: str
    created_at: datetime

