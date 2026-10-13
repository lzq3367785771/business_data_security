from typing import Literal

from pydantic import BaseModel, Field


ReviewStatus = Literal[
    "confirmed",
    "rejected",
]


class SensitiveFieldReviewRequest(BaseModel):
    review_status: ReviewStatus

    note: str | None = Field(
        default=None,
        max_length=500,
    )