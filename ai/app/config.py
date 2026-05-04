from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API Keys (Bisa diisi mana yang mau dipakai)
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "OPENAI_KEY"),
    )
    groq_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY", "GROQ_API_TOKEN"),
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Google Calendar
    google_calendar_credentials_path: str = "./credentials.json"
    google_calendar_token_path: str = "./token.json"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

settings = Settings() # type: ignore