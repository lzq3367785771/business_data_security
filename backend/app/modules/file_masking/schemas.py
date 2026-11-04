
from typing import Literal

from pydantic import BaseModel, Field


SensitiveType = Literal[
    "name",
    "phone",
    "id_card",
    "email",
    "address",
    "salary",
]


class MaskColumnSelection(BaseModel):
    """
    用户确认需要脱敏的表格列。
    """

    sheet_name: str = Field(
        min_length=1,
        max_length=100,
    )

    column_index: int = Field(
        ge=1,
        le=16384,
    )

    sensitive_type: SensitiveType


class MaskRequest(BaseModel):
    """
    文件脱敏执行请求。
    """

    selections: list[MaskColumnSelection] = Field(
        min_length=1,
        max_length=100,
    )
