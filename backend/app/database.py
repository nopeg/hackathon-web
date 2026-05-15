from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settingsInstance

databaseUrl = settingsInstance.DATABASE_URL

engineInstance = create_engine(databaseUrl)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engineInstance
)

BaseModel = declarative_base()

def getDatabaseConnection():
    databaseSession = SessionLocal()
    try:
        yield databaseSession
    finally:
        databaseSession.close()