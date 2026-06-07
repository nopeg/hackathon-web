from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import UserRole
from app.schemas.hackathonSchema import HackathonSimpleResponse

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER

class UserResponse(UserBase):
    id: int
    role: UserRole
    isVerified: bool

    model_config = ConfigDict(from_attributes=True)

class ParticipationInfo(BaseModel):
    hackathonId: int
    hackathonTitle: str
    role: str
    teamId: Optional[int] = None
    teamName: Optional[str] = None
    registrationDate: datetime

class UserProfileResponse(UserResponse):
    createdHackathons: List[HackathonSimpleResponse] = []
    participations: List[ParticipationInfo] = []

class UserHackathonsResponse(BaseModel):
    created: List[HackathonSimpleResponse]
    participated: List[HackathonSimpleResponse]