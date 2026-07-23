from dataclasses import dataclass
from datetime import datetime

from app.models.role import EmployeeRole
from app.models.team import EmployeeTeam


@dataclass
class Employee:

    id: int

    telegram_id: int

    username: str | None

    full_name: str

    phone: str | None

    role: EmployeeRole

    team: EmployeeTeam | None

    is_active: bool

    created_at: datetime | None
