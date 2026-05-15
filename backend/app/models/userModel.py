from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashedPassword = Column(String, nullable=False)
    isVerified = Column(Boolean, default=False)
    createdAt = Column(DateTime, server_default=func.now())