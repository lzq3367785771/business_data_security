from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Float,
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

    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
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



class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 凭据唯一标识
    # 例如 CRM_MYSQL_CREDENTIAL
    credential_key: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    # 凭据名称
    credential_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    # 凭据类型
    # mysql_password / api_token / api_key
    credential_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    # 账号名，例如 bdas_scanner
    username: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    # 加密后的密码 / Token
    # 永远不保存明文
    secret_ciphertext: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
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



class DatabaseAsset(Base):
    __tablename__ = "database_assets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 来源数据源
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id"),
        index=True,
        nullable=False,
    )

    database_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
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


class TableAsset(Base):
    __tablename__ = "table_assets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    database_asset_id: Mapped[int] = mapped_column(
        ForeignKey("database_assets.id"),
        index=True,
        nullable=False,
    )

    table_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    table_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    row_count: Mapped[int | None] = mapped_column(
        Integer,
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


class ColumnAsset(Base):
    __tablename__ = "column_assets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    table_asset_id: Mapped[int] = mapped_column(
        ForeignKey("table_assets.id"),
        index=True,
        nullable=False,
    )

    column_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    data_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    is_nullable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_primary_key: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    ordinal_position: Mapped[int | None] = mapped_column(
        Integer,
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


class SensitiveFieldProfile(Base):
    __tablename__ = "sensitive_field_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 对应字段资产
    column_asset_id: Mapped[int] = mapped_column(
        ForeignKey("column_assets.id"),
        unique=True,
        index=True,
        nullable=False,
    )

    # 是否敏感
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 敏感类型
    # name / phone / id_card / email / address ...
    sensitive_type: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        nullable=True,
    )

    # 中文名称
    # 姓名 / 手机号 / 身份证号 / 邮箱 / 详细地址
    sensitive_label: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    # L1 / L2 / L3 / L4
    sensitivity_level: Mapped[str] = mapped_column(
        String(16),
        default="L1",
        index=True,
        nullable=False,
    )

    # rule / content / ai / manual / hybrid
    detection_method: Mapped[str] = mapped_column(
        String(32),
        default="rule",
        nullable=False,
    )

    # 0~1
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # pending / confirmed / rejected
    review_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
        nullable=False,
    )

    # 命中的规则，例如 field_name:id_card
    detection_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
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