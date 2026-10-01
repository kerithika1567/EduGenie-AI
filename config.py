import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    enable_local_model: bool = False
    local_model_name: str = "MBZUAI/LaMini-Flan-T5-248M"
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    """Returns updated settings by reloading .env on demand."""
    load_dotenv(override=True)
    return Settings(_env_file=".env")

settings = get_settings()
