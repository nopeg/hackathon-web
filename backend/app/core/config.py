from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    SECRET_KEY: str = "31b60b1e2545431cb25da16dd86b767f93e76754f1fe6aba8363b31ddb1af098"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DB_USER: str = Field(default="hackathon", alias="DB_USER")
    DB_PASSWORD: str = Field(default="password", alias="DB_PASSWORD")
    DB_NAME: str = Field(default="hackathon_db", alias="DB_NAME")
    DB_HOST: str = Field(default="db", alias="DB_HOST")
    DB_PORT: str = Field(default="5432", alias="DB_PORT")

    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settingsInstance = Settings()

if not settingsInstance.DATABASE_URL:
    settingsInstance.DATABASE_URL = (
        f"postgresql://{settingsInstance.DB_USER}:{settingsInstance.DB_PASSWORD}"
        f"@{settingsInstance.DB_HOST}:{settingsInstance.DB_PORT}/{settingsInstance.DB_NAME}"
    )