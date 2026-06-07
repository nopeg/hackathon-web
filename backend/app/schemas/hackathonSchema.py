from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import VotingType, ContextRole

class HackathonBase(BaseModel):
    title: str
    description: Optional[str] = None
    prizePool: Optional[str] = None
    location: str
    isOnline: bool = True
    isPrivate: bool = False
    votingType: VotingType = VotingType.ALL_USERS
    startDate: datetime
    endDate: datetime
    registrationStart: datetime
    maxParticipants: Optional[int] = None
    minTeamSize: int = 1
    maxTeamSize: int = 5
    imageUrl: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class HackathonCreate(HackathonBase):
    pass

class HackathonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prizePool: Optional[str] = None
    location: Optional[str] = None
    isOnline: Optional[bool] = None
    isPrivate: Optional[bool] = None
    votingType: Optional[VotingType] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    registrationStart: Optional[datetime] = None
    maxParticipants: Optional[int] = None
    minTeamSize: Optional[int] = None
    maxTeamSize: Optional[int] = None
    imageUrl: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class HackathonResponse(HackathonBase):
    id: int
    currentParticipants: int
    organizerId: int
    status: int

class HackathonSimpleResponse(BaseModel):
    id: int
    title: str
    startDate: datetime
    endDate: datetime
    status: int

    model_config = ConfigDict(from_attributes=True)

class ParticipantResponse(BaseModel):
    id: int
    hackathonId: int
    userId: int
    teamId: Optional[int] = None
    contextRole: str

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class AllowUserRequest(BaseModel):
    username: str