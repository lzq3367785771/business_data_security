from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
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