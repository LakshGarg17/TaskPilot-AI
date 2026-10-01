from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    APP_NAME: str = "TaskPilot AI"
    APP_VERSION: str = "0.1.0"
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_long_12345"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    MOCK_MODE: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://taskpilot:taskpilot_secret_password@localhost:5432/taskpilot"

    # AI & Search
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_PROVIDER: str = "tavily"

    # SMTP (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@taskpilot.local"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    @model_validator(mode="after")
    def validate_keys_in_prod_mode(self) -> "Settings":
        if not self.MOCK_MODE:
            if not self.OPENAI_API_KEY or self.OPENAI_API_KEY.startswith("your_"):
                raise ValueError("OPENAI_API_KEY is required and cannot be empty or placeholder when MOCK_MODE=false")
            if not self.SEARCH_API_KEY or self.SEARCH_API_KEY.startswith("your_"):
                raise ValueError("SEARCH_API_KEY is required and cannot be empty or placeholder when MOCK_MODE=false")
        return self


settings = Settings()
