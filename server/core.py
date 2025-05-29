from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):

    MONGODB_URL: str
    DATABASE_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

# print(f"CORE.PY - Loaded Settings: MONGODB_URL='{settings.MONGODB_URL}', DATABASE_NAME='{settings.DATABASE_NAME}'")
