from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Hackathon(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    organizerId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    registrationStart = Column(DateTime, nullable=False)
    imageUrl = Column(String)
    maxParticipants = Column(Integer, nullable=False)
    currentParticipants = Column(Integer, default=0)
    status = Column(Integer, default=0)
    createdAt = Column(DateTime, server_default=func.now())