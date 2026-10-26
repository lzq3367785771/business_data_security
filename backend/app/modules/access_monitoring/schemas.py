from typing import Literal

from pydantic import BaseModel


class AnomalyStatusUpdate(BaseModel):
    status: Literal[
        "open",
        "confirmed",
        "ignored",
        "resolved",
    ]