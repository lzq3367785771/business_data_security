from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
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




class BusinessSystem(Base):
    __tablename__ = "business_systems"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 系统唯一编码，例如 CRM、HR、FINANCE
    system_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    # 系统名称
    system_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    # 系统类型：
    # web / app / api / mixed
    system_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    # 环境：
    # dev / test / prod
    environment: Mapped[str] = mapped_column(
        String(32),
        default="test",
        nullable=False,
    )

    # 责任部门
    owner_department: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    # 系统访问地址
    base_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 描述
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # active / inactive
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )



class DataSource(Base):
    __tablename__ = "data_sources"

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "source_code",
            name="uq_data_source_system_code",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 所属业务系统
    system_id: Mapped[int] = mapped_column(
        ForeignKey("business_systems.id"),
        index=True,
        nullable=False,
    )

    # 数据源编码
    # 例如 CRM_MYSQL
    source_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # 数据源名称
    source_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    # mysql / api / file
    source_type: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )

    # dev / test / prod
    environment: Mapped[str] = mapped_column(
        String(32),
        default="test",
        nullable=False,
    )

    # 数据库类数据源使用
    host: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    database_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    # API 数据源使用
    base_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 文件数据源使用
    file_root: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # none / password / token / api_key
    auth_type: Mapped[str] = mapped_column(
        String(32),
        default="none",
        nullable=False,
    )

    # 后续指向独立凭据中心
    # 当前禁止直接保存明文密码
    secret_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )