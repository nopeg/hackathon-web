from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    secretKey: str = "31b60b1e2545431cb25da16dd86b767f93e76754f1fe6aba8363b31ddb1af098"
    algorithm: str = "HS256"
    accessTokenExpireMinutes: int = 30

    dbUser: str = Field(default="hackathon", alias="DB_USER")
    dbPassword: str = Field(default="password", alias="DB_PASSWORD")
    dbName: str = Field(default="hackathon_db", alias="DB_NAME")
    dbHost: str = Field(default="db", alias="DB_HOST")
    dbPort: str = Field(default="5432", alias="DB_PORT")

    databaseUrl: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settingsInstance = Settings()

if not settingsInstance.databaseUrl:
    settingsInstance.databaseUrl = (
        f"postgresql://{settingsInstance.dbUser}:{settingsInstance.dbPassword}"
        f"@{settingsInstance.dbHost}:{settingsInstance.dbPort}/{settingsInstance.dbName}"
    )