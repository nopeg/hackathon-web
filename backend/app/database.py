from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settingsInstance

databaseUrl = settingsInstance.DATABASE_URL

engine = create_engine(settingsInstance.DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
BaseModel = declarative_base()

def getDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()