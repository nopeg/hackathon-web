from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import getDB
from app.models.userModel import User
from app.models.hackathonModel import Hackathon, Participant, Team
from app.models.enums import HackathonStatus
from app.schemas.userSchema import UserResponse, UserProfileResponse, UserHackathonsResponse, ParticipationInfo
from app.schemas.hackathonSchema import HackathonSimpleResponse
from app.core.security import getCurrentUser

router = APIRouter(prefix="/users", tags=["users"])

def getCurrentUserFromDB(username: str = Depends(getCurrentUser), db: Session = Depends(getDB)) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def compute_status_for_hackathon(hackathon: Hackathon) -> int:
    now = datetime.now(timezone.utc)
    start_date = hackathon.startDate
    end_date = hackathon.endDate
    reg_start = hackathon.registrationStart

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if reg_start.tzinfo is None:
        reg_start = reg_start.replace(tzinfo=timezone.utc)

    if now > end_date:
        return 3
    if now >= start_date:
        return 2
    if now >= reg_start:
        return 1
    return 0

def hackathon_to_simple_response(hackathon: Hackathon) -> HackathonSimpleResponse:
    return HackathonSimpleResponse(
        id=hackathon.id,
        title=hackathon.title,
        startDate=hackathon.startDate,
        endDate=hackathon.endDate,
        status=compute_status_for_hackathon(hackathon)
    )

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(currentUser: User = Depends(getCurrentUserFromDB), db: Session = Depends(getDB)):
    created_hackathons = db.query(Hackathon).filter(Hackathon.organizerId == currentUser.id).all()
    created_responses = [hackathon_to_simple_response(h) for h in created_hackathons]

    participations = db.query(Participant).filter(Participant.userId == currentUser.id).all()
    participation_responses = []
    for p in participations:
        hackathon = db.query(Hackathon).filter(Hackathon.id == p.hackathonId).first()
        team_name = None
        if p.teamId:
            team = db.query(Team).filter(Team.id == p.teamId).first()
            team_name = team.name if team else None
        participation_responses.append(ParticipationInfo(
            hackathonId=p.hackathonId,
            hackathonTitle=hackathon.title if hackathon else "Unknown",
            role=p.contextRole,
            teamId=p.teamId,
            teamName=team_name,
            registrationDate=p.registrationDate
        ))

    return UserProfileResponse(
        id=currentUser.id,
        username=currentUser.username,
        email=currentUser.email,
        role=currentUser.role,
        isVerified=currentUser.isVerified,
        createdHackathons=created_responses,
        participations=participation_responses
    )

@router.get("/{user_id}/hackathons", response_model=UserHackathonsResponse)
def get_user_hackathons(user_id: int, currentUser: User = Depends(getCurrentUserFromDB), db: Session = Depends(getDB)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    created_hackathons = db.query(Hackathon).filter(Hackathon.organizerId == user.id).all()
    created_responses = [hackathon_to_simple_response(h) for h in created_hackathons]

    participations = db.query(Participant).filter(Participant.userId == user.id).all()
    participated_hackathons = []
    for p in participations:
        hackathon = db.query(Hackathon).filter(Hackathon.id == p.hackathonId).first()
        if hackathon:
            participated_hackathons.append(hackathon)

    participated_responses = [hackathon_to_simple_response(h) for h in participated_hackathons]

    return UserHackathonsResponse(
        created=created_responses,
        participated=participated_responses
    )