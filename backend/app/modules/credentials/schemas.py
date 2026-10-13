from typing import Literal

from pydantic import BaseModel, Field


CredentialType = Literal[
    "mysql_password",
    "api_token",
    "api_key",
]


class CredentialCreate(BaseModel):
    """
    创建安全凭据
    """

    credential_key: str = Field(
        min_length=2,
        max_length=128,
    )

    credential_name: str = Field(
        min_length=2,
        max_length=128,
    )

    credential_type: CredentialType

    username: str | None = Field(
        default=None,
        max_length=128,
    )

    secret: str = Field(
        min_length=1,
        max_length=1000,
    )