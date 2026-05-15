from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.database import BaseModel
from app.core.config import settingsInstance

alembicConfig = context.config

if alembicConfig.config_file_name is not None:
    fileConfig(alembicConfig.config_file_name)

targetMetadata = BaseModel.metadata

def runMigrationsOffline() -> None:
    urlAddress = settingsInstance.DATABASE_URL
    context.configure(
        url=urlAddress,
        target_metadata=targetMetadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def runMigrationsOnline() -> None:
    connectableEngine = engine_from_config(
        alembicConfig.get_section(alembicConfig.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectableEngine.connect() as databaseConnection:
        context.configure(
            connection=databaseConnection, 
            target_metadata=targetMetadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    runMigrationsOffline()
else:
    runMigrationsOnline()