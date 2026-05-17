from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    hackathonId: int

class TeamJoin(BaseModel):
    inviteCode: str = Field(..., min_length=6, max_length=8)

class TeamMemberUserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class TeamMemberResponse(BaseModel):
    id: int
    userId: int
    user: TeamMemberUserResponse

    class Config:
        from_attributes = True

class TeamResponse(BaseModel):
    id: int
    name: str
    inviteCode: str
    hackathonId: int
    creatorId: int
    createdAt: datetime

    class Config:
        from_attributes = True

class TeamDetailResponse(TeamResponse):
    members: List[TeamMemberResponse]

    class Config:
        from_attributes = True