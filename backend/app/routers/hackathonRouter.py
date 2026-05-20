from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import getDB
from app.models.userModel import User
from app.models.hackathonModel import Hackathon, Participant
from app.schemas.hackathonSchema import HackathonCreate, HackathonResponse, HackathonUpdate, ParticipantResponse
from app.core.security import getCurrentUser

router = APIRouter(prefix="/hackathons", tags=["hackathons"])

def getCurrentUserFromDB(username: str = Depends(getCurrentUser), db: Session = Depends(getDB)) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("", response_model=HackathonResponse, status_code=status.HTTP_201_CREATED)
def createHackathon(hackathonIn: HackathonCreate, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    if hackathonIn.minTeamSize > hackathonIn.maxTeamSize:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="minTeamSize cannot be greater than maxTeamSize")

    now = datetime.now(timezone.utc)
    reg_start = hackathonIn.registrationStart
    if reg_start.tzinfo is None:
        reg_start = reg_start.replace(tzinfo=timezone.utc)

    if reg_start < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration start cannot be in the past")

    newHackathon = Hackathon(
        title=hackathonIn.title,
        description=hackathonIn.description,
        prizePool=hackathonIn.prizePool,
        location=hackathonIn.location,
        isOnline=hackathonIn.isOnline,
        isPrivate=hackathonIn.isPrivate,
        votingType=hackathonIn.votingType,
        startDate=hackathonIn.startDate,
        endDate=hackathonIn.endDate,
        registrationStart=hackathonIn.registrationStart,
        maxParticipants=hackathonIn.maxParticipants,
        organizerId=currentUser.id,
        minTeamSize=hackathonIn.minTeamSize,
        maxTeamSize=hackathonIn.maxTeamSize,
        imageUrl=hackathonIn.imageUrl
    )
    db.add(newHackathon)
    db.commit()
    db.refresh(newHackathon)
    return newHackathon

@router.get("", response_model=List[HackathonResponse])
def getHackathons(skip: int = 0, limit: int = 10, db: Session = Depends(getDB)):
    return db.query(Hackathon).order_by(Hackathon.startDate.asc()).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=HackathonResponse)
def getHackathon(id: int, db: Session = Depends(getDB)):
    hackathon = db.query(Hackathon).filter(Hackathon.id == id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    return hackathon

@router.put("/{id}", response_model=HackathonResponse)
def updateHackathon(id: int, hackathonIn: HackathonUpdate, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    hackathon = db.query(Hackathon).filter(Hackathon.id == id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.organizerId != currentUser.id and currentUser.role.upper() not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    updateData = hackathonIn.model_dump(exclude_unset=True)
    if "minTeamSize" in updateData or "maxTeamSize" in updateData:
        minSize = updateData.get("minTeamSize", hackathon.minTeamSize)
        maxSize = updateData.get("maxTeamSize", hackathon.maxTeamSize)
        if minSize > maxSize:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="minTeamSize cannot be greater than maxTeamSize")

    for key, value in updateData.items():
        setattr(hackathon, key, value)

    db.commit()
    db.refresh(hackathon)
    return hackathon

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deleteHackathon(id: int, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    hackathon = db.query(Hackathon).filter(Hackathon.id == id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.organizerId != currentUser.id and currentUser.role.upper() not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    db.delete(hackathon)
    db.commit()
    return None

@router.post("/{id}/register", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def registerForHackathon(id: int, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    hackathon = db.query(Hackathon).filter(Hackathon.id == id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.organizerId == currentUser.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creators cannot participate in their own hackathons")

    now = datetime.now(timezone.utc)
    reg_start = hackathon.registrationStart
    if reg_start.tzinfo is None:
        reg_start = reg_start.replace(tzinfo=timezone.utc)

    if now < reg_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration has not started yet")
    if now > hackathon.startDate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration closed, hackathon already started")

    alreadyRegistered = db.query(Participant).filter(
        Participant.hackathonId == id,
        Participant.userId == currentUser.id
    ).first()
    if alreadyRegistered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already registered for this hackathon")

    if hackathon.maxParticipants is not None and hackathon.currentParticipants >= hackathon.maxParticipants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hackathon is full")

    participant = Participant(hackathonId=id, userId=currentUser.id, teamId=None, contextRole="PARTICIPANT")
    hackathon.currentParticipants += 1

    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant