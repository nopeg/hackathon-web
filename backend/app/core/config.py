import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    secretKey: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    accessTokenExpireMinutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    dbUser: str = Field(alias="DB_USER")
    dbPassword: str = Field(alias="DB_PASSWORD")
    dbName: str = Field(alias="DB_NAME")
    dbHost: str = Field(alias="DB_HOST")
    dbPort: str = Field(alias="DB_PORT")

    smtpHost: str = Field(default="", alias="SMTP_HOST")
    smtpPort: int = Field(default=0, alias="SMTP_PORT")
    smtpUser: str = Field(default="", alias="SMTP_USER")
    smtpPassword: str = Field(default="", alias="SMTP_PASSWORD")

    databaseUrl: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settingsInstance = Settings()

if not settingsInstance.databaseUrl:
    settingsInstance.databaseUrl = (
        f"postgresql://{settingsInstance.dbUser}:{settingsInstance.dbPassword}"
        f"@{settingsInstance.dbHost}:{settingsInstance.dbPort}/{settingsInstance.dbName}"
    )