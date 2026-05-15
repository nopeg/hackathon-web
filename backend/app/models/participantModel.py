from sqlalchemy import Column, Integer, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.sql import func
from app.database import BaseModel

class Participant(BaseModel):
    __tablename__ = "hackathon_participants"

    hackathonId = Column(Integer, ForeignKey("hackathons.id", ondelete="CASCADE"), nullable=False)
    userId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    registrationDate = Column(DateTime, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("hackathonId", "userId"),
    )