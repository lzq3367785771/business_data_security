from typing import Literal

from pydantic import BaseModel, Field


SystemType = Literal[
    "web",
    "app",
    "api",
    "mixed",
]

EnvironmentType = Literal[
    "dev",
    "test",
    "prod",
]

SystemStatus = Literal[
    "active",
    "inactive",
]


class BusinessSystemCreate(BaseModel):
    """
    创建业务系统
    """

    system_code: str = Field(
        min_length=2,
        max_length=64,
        description="系统唯一编码，例如 CRM、HR、FINANCE",
    )

    system_name: str = Field(
        min_length=2,
        max_length=128,
    )

    system_type: SystemType

    environment: EnvironmentType = "test"

    owner_department: str | None = Field(
        default=None,
        max_length=128,
    )

    base_url: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class BusinessSystemUpdate(BaseModel):
    """
    修改业务系统基本信息。

    system_code 暂时不允许修改，
    因为后续大量模块会依赖这个系统标识。
    """

    system_name: str = Field(
        min_length=2,
        max_length=128,
    )

    system_type: SystemType

    environment: EnvironmentType

    owner_department: str | None = Field(
        default=None,
        max_length=128,
    )

    base_url: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class BusinessSystemStatusUpdate(BaseModel):
    """
    启用 / 停用业务系统
    """

    status: SystemStatus