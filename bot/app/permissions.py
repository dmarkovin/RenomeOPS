from enum import Enum, auto
from typing import Set, Optional
from app.database.models import User, UserRole


class Permission(Enum):
    """Перечень всех прав, доступных в системе"""
    
    # ===== Заявки (Tasks) =====
    # Просмотр
    TASK_VIEW_ALL = auto()          # Просмотр всех заявок (админ/консьерж/директор)
    TASK_VIEW_TEAM = auto()         # Просмотр заявок своей команды (исполнители)
    TASK_VIEW_OWN = auto()          # Просмотр только своих заявок (все)
    TASK_VIEW_CHECKING = auto()     # Просмотр задач на проверке
    
    # Действия
    TASK_CREATE = auto()            # Создание заявок
    TASK_ASSIGN = auto()            # Назначение на исполнителя/команду
    TASK_TAKE = auto()              # Взятие задачи в работу
    TASK_PAUSE = auto()             # Приостановка задачи
    TASK_RESUME = auto()            # Возобновление задачи
    TASK_CHECK = auto()             # Отправка на проверку
    TASK_CLOSE = auto()             # Закрытие задачи
    TASK_REWORK = auto()            # Возврат на доработку
    
    # Архив
    TASK_VIEW_ARCHIVE = auto()      # Просмотр архива
    TASK_VIEW_ARCHIVE_ALL = auto()  # Просмотр всего архива (без фильтрации)
    TASK_VIEW_ARCHIVE_TEAM = auto() # Просмотр архива своей команды
    
    # ===== Пропуска (Passes) =====
    PASS_VIEW_ALL = auto()          # Просмотр всех пропусков
    PASS_CREATE = auto()            # Создание пропусков
    PASS_CHECKIN = auto()           # Отметка въезда
    PASS_CHECKOUT = auto()          # Отметка выезда
    PASS_COMPLETE = auto()          # Завершение пропуска
    PASS_CLOSE = auto()             # Закрытие пропуска (expired)
    
    # ===== Доставка, ключи, документы (Reception) =====
    DELIVERY_MANAGE = auto()        # Управление доставкой (создание, получение, завершение)
    KEYS_MANAGE = auto()            # Управление ключами
    DOCUMENTS_MANAGE = auto()       # Управление документами
    
    # ===== Платные услуги (Services) =====
    SERVICE_ORDER = auto()          # Заказ услуг
    SERVICE_MANAGE = auto()         # Управление услугами (создание, редактирование, удаление)
    
    # ===== Сотрудники (Employees) =====
    EMPLOYEE_VIEW = auto()          # Просмотр списка сотрудников
    EMPLOYEE_MANAGE = auto()        # Управление сотрудниками (блокировка, активация, смена роли)
    
    # ===== Обходы (Patrol) =====
    PATROL_CREATE = auto()          # Создание обходов
    PATROL_VIEW = auto()            # Просмотр обходов
    PATROL_COMPLETE = auto()        # Завершение обходов
    
    # ===== Статистика =====
    STATISTICS_VIEW = auto()        # Просмотр статистики
    
    # ===== Настройки =====
    SETTINGS_MANAGE = auto()        # Управление настройками


# ===== Маппинг ролей на права =====
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Полный доступ
        Permission.TASK_VIEW_ALL,
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_VIEW_CHECKING,
        Permission.TASK_CREATE,
        Permission.TASK_ASSIGN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_RESUME,
        Permission.TASK_CHECK,
        Permission.TASK_CLOSE,
        Permission.TASK_REWORK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_ALL,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.PASS_VIEW_ALL,
        Permission.PASS_CREATE,
        Permission.PASS_CHECKIN,
        Permission.PASS_CHECKOUT,
        Permission.PASS_COMPLETE,
        Permission.PASS_CLOSE,
        Permission.DELIVERY_MANAGE,
        Permission.KEYS_MANAGE,
        Permission.DOCUMENTS_MANAGE,
        Permission.SERVICE_ORDER,
        Permission.SERVICE_MANAGE,
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_MANAGE,
        Permission.PATROL_CREATE,
        Permission.PATROL_VIEW,
        Permission.PATROL_COMPLETE,
        Permission.STATISTICS_VIEW,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.DIRECTOR: {
        Permission.TASK_VIEW_ALL,
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_VIEW_CHECKING,
        Permission.TASK_CREATE,
        Permission.TASK_ASSIGN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_CHECK,
        Permission.TASK_CLOSE,
        Permission.TASK_REWORK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_ALL,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.PASS_VIEW_ALL,
        Permission.PASS_CREATE,
        Permission.PASS_CHECKIN,
        Permission.PASS_CHECKOUT,
        Permission.PASS_COMPLETE,
        Permission.PASS_CLOSE,
        Permission.SERVICE_ORDER,
        Permission.STATISTICS_VIEW,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.CONCIERGE: {
        Permission.TASK_VIEW_ALL,
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_VIEW_CHECKING,
        Permission.TASK_CREATE,
        Permission.TASK_ASSIGN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_CHECK,
        Permission.TASK_CLOSE,
        Permission.TASK_REWORK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_ALL,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.PASS_VIEW_ALL,
        Permission.PASS_CREATE,
        Permission.PASS_CHECKIN,
        Permission.PASS_CHECKOUT,
        Permission.PASS_COMPLETE,
        Permission.PASS_CLOSE,
        Permission.DELIVERY_MANAGE,
        Permission.KEYS_MANAGE,
        Permission.DOCUMENTS_MANAGE,
        Permission.SERVICE_ORDER,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.TECHNICIAN: {
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_RESUME,
        Permission.TASK_CHECK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.CLEANER: {
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_RESUME,
        Permission.TASK_CHECK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.SECURITY: {
        Permission.TASK_VIEW_TEAM,
        Permission.TASK_VIEW_OWN,
        Permission.TASK_TAKE,
        Permission.TASK_PAUSE,
        Permission.TASK_RESUME,
        Permission.TASK_CHECK,
        Permission.TASK_VIEW_ARCHIVE,
        Permission.TASK_VIEW_ARCHIVE_TEAM,
        Permission.PASS_VIEW_ALL,
        Permission.PASS_CREATE,
        Permission.PASS_CHECKIN,
        Permission.PASS_CHECKOUT,
        Permission.PASS_COMPLETE,
        Permission.PATROL_CREATE,
        Permission.PATROL_VIEW,
        Permission.PATROL_COMPLETE,
        Permission.SETTINGS_MANAGE,
    },
}


# ===== Функции проверки прав =====

def has_permission(user: Optional[User], permission: Permission) -> bool:
    """
    Проверяет, имеет ли пользователь указанное право.
    Если пользователь не передан или неактивен, возвращает False.
    """
    if not user or not user.active:
        return False
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def has_any_permission(user: Optional[User], permissions: list[Permission]) -> bool:
    """Проверяет, есть ли у пользователя хотя бы одно из перечисленных прав."""
    if not user or not user.active:
        return False
    user_perms = ROLE_PERMISSIONS.get(user.role, set())
    return any(p in user_perms for p in permissions)


def has_all_permissions(user: Optional[User], permissions: list[Permission]) -> bool:
    """Проверяет, есть ли у пользователя все перечисленные права."""
    if not user or not user.active:
        return False
    user_perms = ROLE_PERMISSIONS.get(user.role, set())
    return all(p in user_perms for p in permissions)


# ===== Утилиты для проверки конкретных сценариев =====

def can_view_task(user: Optional[User], task) -> bool:
    """
    Проверяет, может ли пользователь просматривать задачу.
    Учитывает права и принадлежность к команде.
    """
    if not user:
        return False
    # Админ/консьерж/директор могут видеть всё
    if has_permission(user, Permission.TASK_VIEW_ALL):
        return True
    # Исполнитель видит свои задачи и задачи своей команды
    if has_permission(user, Permission.TASK_VIEW_TEAM) or has_permission(user, Permission.TASK_VIEW_OWN):
        if task.assigned_to == user.id:
            return True
        if task.assigned_team == user.team:
            return True
    return False


def can_take_task(user: Optional[User], task) -> bool:
    """Проверяет, может ли пользователь взять задачу."""
    if not user:
        return False
    if not has_permission(user, Permission.TASK_TAKE):
        return False
    if task.status in ("closed", "checking"):
        return False
    if task.assigned_to is not None:
        # Если задача уже назначена, взять могут только админ/консьерж/директор
        if not has_permission(user, Permission.TASK_ASSIGN):
            return False
    # Если задача назначена на команду, пользователь должен быть в этой команде
    if task.assigned_team and task.assigned_team != user.team:
        return False
    return True


def can_assign_task(user: Optional[User]) -> bool:
    """Проверяет, может ли пользователь назначать задачи."""
    return has_permission(user, Permission.TASK_ASSIGN)


def can_check_task(user: Optional[User], task) -> bool:
    """Проверяет, может ли пользователь отправить задачу на проверку."""
    if not user:
        return False
    if not has_permission(user, Permission.TASK_CHECK):
        return False
    if task.status not in ("in_progress", "paused"):
        return False
    # Исполнитель может отправить свою задачу
    if task.assigned_to == user.id:
        return True
    # Член команды может отправить задачу, если она назначена на команду и ещё не взята
    if task.assigned_team == user.team and task.assigned_to is None:
        return True
    # Админ/консьерж/директор могут отправить любую
    if has_permission(user, Permission.TASK_ASSIGN):
        return True
    return False


def can_close_task(user: Optional[User]) -> bool:
    """Проверяет, может ли пользователь закрывать задачи."""
    return has_permission(user, Permission.TASK_CLOSE)
