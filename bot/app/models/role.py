from enum import Enum


class EmployeeRole(str, Enum):

    SUPER_ADMIN = "SUPER_ADMIN"

    DIRECTOR = "DIRECTOR"

    CONCIERGE = "CONCIERGE"

    TECH_SPECIALIST = "TECH_SPECIALIST"

    CLEANING = "CLEANING"

    SECURITY = "SECURITY"
