from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(32), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class Customer(Base):
    __tablename__ = "demo_customers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(32), nullable=False
    )

    id_card: Mapped[str] = mapped_column(
        String(32), nullable=False
    )


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    resource: Mapped[str] = mapped_column(
        String(128), index=True, nullable=False
    )

    allowed_roles: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    effect: Mapped[str] = mapped_column(
        String(16), nullable=False
    )

    mask_fields: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    request_id: Mapped[str] = mapped_column(
        String(36), index=True, nullable=False
    )

    trace_id: Mapped[str] = mapped_column(
        String(36), index=True, nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(64), nullable=False
    )

    resource: Mapped[str] = mapped_column(
        String(128), nullable=False
    )

    result: Mapped[str] = mapped_column(
        String(16), nullable=False
    )

    policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("policy_rules.id"),
        nullable=True
    )

    object_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False
    )