from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, BigInteger, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

# ===========================
# Роли и команды
# ===========================
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DIRECTOR = "DIRECTOR"
    CONCIERGE = "CONCIERGE"
    TECHNICIAN = "TECHNICIAN"
    CLEANER = "CLEANER"
    SECURITY = "SECURITY"

class Team(str, enum.Enum):
    ADMIN_TEAM = "ADMIN_TEAM"
    DIRECTOR_TEAM = "DIRECTOR_TEAM"
    TEAM_TECH = "TEAM_TECH"
    TEAM_CLEANING = "TEAM_CLEANING"
    TEAM_SECURITY = "TEAM_SECURITY"
    TEAM_CONCIERGE = "TEAM_CONCIERGE"

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
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    team = Column(Enum(Team), nullable=True)
    active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, nullable=True)

    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    comments = relationship("Comment", back_populates="author")

# ===========================
# Задача
# ===========================
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=TaskStatus.CREATED.value, nullable=False)
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
    video_ids = Column(JSON, default=list)

    creator = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    comments = relationship("Comment", back_populates="task")
    photos = relationship("TaskPhoto", back_populates="task")
    history = relationship("TaskHistory", back_populates="task")

# ===========================
# Комментарий к задаче
# ===========================
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")

# ===========================
# Фото к задаче
# ===========================
class TaskPhoto(Base):
    __tablename__ = "task_photos"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    telegram_file_id = Column(String(255), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="photos")

# ===========================
# История задачи
# ===========================
class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="history")
    user = relationship("User")

# ===========================
# Пропуск
# ===========================
class Pass(Base):
    __tablename__ = "passes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False)
    guest_name = Column(String(255), nullable=True)
    car_number = Column(String(20), nullable=True)
    apartment = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")
    comment = Column(Text, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_team = Column(String(50), nullable=True)
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    history = Column(JSON, default=list)
    comments = Column(JSON, default=list)

    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])

# ===========================
# Доставка
# ===========================
class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(255), nullable=False)
    apartment = Column(Integer, nullable=True)
    courier_service = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sender = Column(String(255), nullable=True)
    comments = Column(JSON, default=list)
    history = Column(JSON, default=list)  # добавлено для истории

    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Ключи
# ===========================
class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_number = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="issued")
    issued_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = Column(JSON, default=list)

    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Документы
# ===========================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)  # incoming, outgoing, storage, issued
    number = Column(String(50), nullable=True)
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = Column(JSON, default=list)
    history = Column(JSON, default=list)

    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Обходы
# ===========================
class Patrol(Base):
    __tablename__ = "patrols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    photo_ids = Column(JSON, default=list)
    video_ids = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    status = Column(String(20), default="active")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", foreign_keys=[created_by])

# ===========================
# Платные услуги
# ===========================
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    comment = Column(Text, nullable=True)
    photo_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service = relationship("Service")
    user = relationship("User")

# ===========================
# Настройки пользователя
# ===========================
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    notify_admin = Column(Boolean, default=True)
    notify_task_assigned = Column(Boolean, default=True)
    notify_new_task_team = Column(Boolean, default=True)
    notify_checking = Column(Boolean, default=True)
    notify_security = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
