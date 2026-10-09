from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal[
    "mysql",
    "api",
    "file",
]

EnvironmentType = Literal[
    "dev",
    "test",
    "prod",
]

AuthType = Literal[
    "none",
    "password",
    "token",
    "api_key",
]

SourceStatus = Literal[
    "active",
    "inactive",
]


class DataSourceCreate(BaseModel):

    system_id: int = Field(
        gt=0,
    )

    source_code: str = Field(
        min_length=2,
        max_length=64,
    )

    source_name: str = Field(
        min_length=2,
        max_length=128,
    )

    source_type: SourceType

    environment: EnvironmentType = "test"

    host: str | None = Field(
        default=None,
        max_length=255,
    )

    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )

    database_name: str | None = Field(
        default=None,
        max_length=128,
    )

    username: str | None = Field(
        default=None,
        max_length=128,
    )

    base_url: str | None = Field(
        default=None,
        max_length=255,
    )

    file_root: str | None = Field(
        default=None,
        max_length=500,
    )

    auth_type: AuthType = "none"

    secret_ref: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class DataSourceUpdate(BaseModel):

    source_name: str = Field(
        min_length=2,
        max_length=128,
    )

    environment: EnvironmentType

    host: str | None = Field(
        default=None,
        max_length=255,
    )

    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )

    database_name: str | None = Field(
        default=None,
        max_length=128,
    )

    username: str | None = Field(
        default=None,
        max_length=128,
    )

    base_url: str | None = Field(
        default=None,
        max_length=255,
    )

    file_root: str | None = Field(
        default=None,
        max_length=500,
    )

    auth_type: AuthType

    secret_ref: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class DataSourceStatusUpdate(BaseModel):

    status: SourceStatus