from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    userEmail = Column(String, ForeignKey("users.email", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expiresAt = Column(DateTime(timezone=True), nullable=False)