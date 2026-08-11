from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Numeric,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

# ===========================
# Роли сотрудников
# ===========================
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DIRECTOR = "DIRECTOR"
    CONCIERGE = "CONCIERGE"
    TECHNICIAN = "TECHNICIAN"
    CLEANER = "CLEANER"
    SECURITY = "SECURITY"

# ===========================
# Команды
# ===========================
class Team(str, enum.Enum):
    TEAM_TECH = "TEAM_TECH"
    TEAM_CLEANING = "TEAM_CLEANING"
    TEAM_SECURITY = "TEAM_SECURITY"
    TEAM_CONCIERGE = "TEAM_CONCIERGE"
    ADMIN_TEAM = "ADMIN_TEAM"
    DIRECTOR_TEAM = "DIRECTOR_TEAM"

# ===========================
# Статусы задач
# ===========================
class TaskStatus(str, enum.Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    CHECKING = "checking"
    CLOSED = "closed"
    WAITING = "waiting"
    PAUSED = "paused"

# ===========================
# Пользователь
# ===========================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    invite_code = Column(String(64), unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    team = Column(Enum(Team), nullable=True)
    active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, nullable=True)

# ===========================
# Задача
# ===========================
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="created", nullable=False)
    building = Column(Integer, nullable=True)
    entrance = Column(Integer, nullable=True)
    floor = Column(Integer, nullable=True)
    apartment = Column(Integer, nullable=True)
    location_type = Column(String(50), nullable=True)
    parking_level = Column(Integer, nullable=True)
    parking_spot = Column(Integer, nullable=True)
    cellar = Column(Integer, nullable=True)
    applicant_type = Column(String(20), nullable=True)
    applicant_name = Column(String(255), nullable=True)
    applicant_phone = Column(String(20), nullable=True)
    priority = Column(Integer, default=3)
    is_paid = Column(Boolean, default=False)
    is_feedback = Column(Boolean, default=False)
    is_role_change = Column(Boolean, default=False)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)
    wait_until = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_team = Column(Enum(Team), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    # Новое поле для видео (список file_id)
    video_ids = Column(JSON, default=list)
    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_assigned_to", "assigned_to"),
        Index("ix_tasks_assigned_team", "assigned_team"),
        Index("ix_tasks_created_at", "created_at"),
        Index("ix_tasks_is_paid", "is_paid"),
    )

    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    photos = relationship("TaskPhoto", back_populates="task", cascade="all, delete-orphan")
    service_order = relationship("ServiceOrder", foreign_keys=[service_order_id])

# ===========================
# Комментарии
# ===========================
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey("tasks.id"))
    author_id = Column(ForeignKey("users.id"))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    task = relationship("Task", back_populates="comments")
    author = relationship("User")

# ===========================
# Фото
# ===========================
class TaskPhoto(Base):
    __tablename__ = "task_photos"
    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey("tasks.id"))
    telegram_file_id = Column(String(255), nullable=False)
    uploaded_by = Column(ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    task = relationship("Task", back_populates="photos")

# ===========================
# История изменений
# ===========================
class TaskHistory(Base):
    __tablename__ = "task_history"
    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey("tasks.id"))
    action = Column(String(100), nullable=False)
    description = Column(Text)
    user_id = Column(ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    task = relationship("Task", back_populates="history")
    user = relationship("User", foreign_keys=[user_id])

# ===========================
# Платные услуги
# ===========================
class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceOrder(Base):
    __tablename__ = "service_orders"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    building = Column(Integer, nullable=True)
    entrance = Column(Integer, nullable=True)
    floor = Column(Integer, nullable=True)
    apartment = Column(Integer, nullable=True)
    parking_floor = Column(Integer, nullable=True)
    parking_spot = Column(Integer, nullable=True)
    cellar = Column(Integer, nullable=True)
    comment = Column(Text)
    photo_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    service = relationship("Service")
    user = relationship("User")

# ===========================
# Пропуска
# ===========================
class Pass(Base):
    __tablename__ = "passes"
    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)
    guest_name = Column(String(255), nullable=True)
    car_number = Column(String(20), nullable=True)
    apartment = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")
    comment = Column(Text)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_team = Column(String(50), nullable=True)
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])

# ===========================
# Доставка (Ресепшен)
# ===========================
class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    recipient = Column(String(255), nullable=False)
    apartment = Column(Integer, nullable=True)
    courier_service = Column(String(255), nullable=True)
    comment = Column(Text)
    photo_ids = Column(JSON, default=list)
    comments = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Ключи (Ресепшен)
# ===========================
class Key(Base):
    __tablename__ = "keys"
    id = Column(Integer, primary_key=True)
    key_number = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=True)
    apartment = Column(Integer, nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="issued")
    comment = Column(Text)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Документы (Ресепшен)
# ===========================
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    doc_type = Column(String(20), nullable=False)
    number = Column(String(50), nullable=True)
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    issued_to = Column(String(255), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    comment = Column(Text)
    apartment = Column(Integer, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Обходы (охрана)
# ===========================
class Patrol(Base):
    __tablename__ = "patrols"
    id = Column(Integer, primary_key=True)
    route = Column(String(255), nullable=False)
    notes = Column(Text)
    status = Column(String(20), default="active")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    creator = relationship("User", foreign_keys=[created_by])
    task = relationship("Task", foreign_keys=[task_id])

# ===========================
# Настройки уведомлений пользователя
# ===========================
class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notify_task_assigned = Column(Boolean, default=True)
    notify_task_mentioned = Column(Boolean, default=True)
    notify_task_status_changed = Column(Boolean, default=True)
    notify_task_comment = Column(Boolean, default=True)
    notify_task_closed = Column(Boolean, default=True)
    notify_new_task_team = Column(Boolean, default=True)
    notify_checking = Column(Boolean, default=True)
    notify_admin = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id])
