from enum import Enum


class EmployeeRole(str, Enum):

    SUPER_ADMIN = "SUPER_ADMIN"

    CONCIERGE = "CONCIERGE"

    DIRECTOR = "DIRECTOR"

    EXECUTOR = "EXECUTOR"
