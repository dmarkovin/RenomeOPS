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
)

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

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


# ===========================
# Статусы задач
# ===========================

class TaskStatus(str, enum.Enum):
    CREATED = "created"

    ACCEPTED = "accepted"

    IN_PROGRESS = "in_progress"

    CHECKING = "checking"

    CLOSED = "closed"


# ===========================
# Пользователь
# ===========================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    telegram_id = Column(
        BigInteger,
        unique=True,
        nullable=True
    )

    invite_code = Column(
        String(64),
        unique=True,
        nullable=False
    )

    username = Column(
        String(100)
    )

    full_name = Column(
        String(255),
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False
    )

    team = Column(
        Enum(Team),
        nullable=True
    )

    active = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    registered_at = Column(
        DateTime,
        nullable=True
    )
# ===========================
# Задача
# ===========================

class Task(Base):

    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text
    )

    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.CREATED,
        nullable=False
    )

    building = Column(
        String(20)
    )

    apartment = Column(
        String(20)
    )

    priority = Column(
        Integer,
        default=3
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    assigned_to = Column(
        Integer,
    ForeignKey("users.id"),
    nullable=True
    )
    assigned_team = Column(
        Enum(Team),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    closed_at = Column(
        DateTime,
        nullable=True
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to]
    )

    comments = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    history = relationship(
        "TaskHistory",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    photos = relationship(
        "TaskPhoto",
        back_populates="task",
        cascade="all, delete-orphan"
    )


# ===========================
# Комментарии
# ===========================

class Comment(Base):

    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        ForeignKey("tasks.id")
    )

    author_id = Column(
        ForeignKey("users.id")
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    task = relationship(
        "Task",
        back_populates="comments"
    )


# ===========================
# Фото
# ===========================

class TaskPhoto(Base):

    __tablename__ = "task_photos"

    id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        ForeignKey("tasks.id")
    )

    telegram_file_id = Column(
        String(255),
        nullable=False
    )

    uploaded_by = Column(
        ForeignKey("users.id")
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    task = relationship(
        "Task",
        back_populates="photos"
    )


# ===========================
# История изменений
# ===========================

class TaskHistory(Base):

    __tablename__ = "task_history"

    id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        ForeignKey("tasks.id")
    )

    action = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text
    )

    user_id = Column(
        ForeignKey("users.id")
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    task = relationship(
        "Task",
        back_populates="history"
    )
