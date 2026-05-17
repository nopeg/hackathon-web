from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settingsInstance

databaseUrl = settingsInstance.databaseUrl

engine = create_engine(settingsInstance.databaseUrl)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

def getDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()