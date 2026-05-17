import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VotingType(str, enum.Enum):
    JUDGES = "JUDGES"
    PARTICIPANTS = "PARTICIPANTS"
    ALL_USERS = "ALL_USERS"

class ContextRole(str, enum.Enum):
    PARTICIPANT = "PARTICIPANT"
    JUDGE = "JUDGE"

class Hackathon(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prizePool = Column(String, nullable=True)
    location = Column(String, nullable=False)
    isOnline = Column(Boolean, default=True)
    isPrivate = Column(Boolean, default=False)
    votingType = Column(String, default="ALL_USERS", nullable=False)
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    registrationDeadline = Column(DateTime, nullable=False)
    maxParticipants = Column(Integer, nullable=True)
    currentParticipants = Column(Integer, default=0)
    organizerId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    minTeamSize = Column(Integer, default=1)
    maxTeamSize = Column(Integer, default=5)

class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    hackathonId = Column(Integer, ForeignKey("hackathons.id", ondelete="CASCADE"), nullable=False)
    userId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    teamId = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    contextRole = Column(String, default="PARTICIPANT", nullable=False)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    inviteCode = Column(String, unique=True, nullable=False)
    hackathonId = Column(Integer, ForeignKey("hackathons.id", ondelete="CASCADE"), nullable=False)
    creatorId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)

class HackathonAllowList(Base):
    __tablename__ = "hackathon_allow_list"

    id = Column(Integer, primary_key=True, index=True)
    hackathonId = Column(Integer, ForeignKey("hackathons.id", ondelete="CASCADE"), nullable=False)
    userId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)