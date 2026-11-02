from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

# =========================
# Backend 路径
# =========================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    BACKEND_DIR
    / ".env"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(
            ENV_FILE
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_env: str = "development"

    database_url: str

    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 60

    frontend_origins: str = (
        "http://127.0.0.1:5173,"
        "http://localhost:5173"
    )

    demo_admin_password: str = ""
    demo_analyst_password: str = ""

    credential_master_key: str 
    
    file_master_key: str

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()