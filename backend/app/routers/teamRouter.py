from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string
from datetime import datetime, timezone

from app.database import getDB
from app.models.userModel import User
from app.models.hackathonModel import Hackathon, Participant, Team
from app.schemas.teamSchema import TeamCreate, TeamJoin, TeamResponse, TeamDetailResponse
from app.core.security import getCurrentUser

router = APIRouter(prefix="/teams", tags=["teams"])

def getCurrentUserFromDB(username: str = Depends(getCurrentUser), db: Session = Depends(getDB)) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def generateInviteCode(db: Session) -> str:
    lettersAndDigits = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(lettersAndDigits) for _ in range(6))
        codeExists = db.query(Team).filter(Team.inviteCode == code).first()
        if not codeExists:
            return code

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def createTeam(teamIn: TeamCreate, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    hackathon = db.query(Hackathon).filter(Hackathon.id == teamIn.hackathonId).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.organizerId == currentUser.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creators cannot create teams for their own hackathons")

    if hackathon.maxTeamSize <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teams are disabled for this hackathon")

    participant = db.query(Participant).filter(
        Participant.hackathonId == hackathon.id,
        Participant.userId == currentUser.id
    ).first()
    if not participant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must register for the hackathon before creating a team")

    if participant.teamId is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already in a team for this hackathon")

    inviteCode = generateInviteCode(db)
    newTeam = Team(
        name=teamIn.name,
        inviteCode=inviteCode,
        hackathonId=teamIn.hackathonId,
        creatorId=currentUser.id
    )
    db.add(newTeam)
    db.flush()

    participant.teamId = newTeam.id
    db.commit()
    db.refresh(newTeam)
    return newTeam

@router.post("/join", response_model=TeamResponse)
def joinTeam(teamJoinIn: TeamJoin, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    team = db.query(Team).filter(Team.inviteCode == teamJoinIn.inviteCode).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code")

    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathonId).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.organizerId == currentUser.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creators cannot join teams in their own hackathons")

    currentTeamMembersCount = db.query(Participant).filter(Participant.teamId == team.id).count()
    if currentTeamMembersCount >= hackathon.maxTeamSize:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team is full")

    participant = db.query(Participant).filter(
        Participant.hackathonId == team.hackathonId,
        Participant.userId == currentUser.id
    ).first()

    if participant and participant.teamId is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already in a team for this hackathon")

    if not participant:
        if hackathon.maxParticipants is not None and hackathon.currentParticipants >= hackathon.maxParticipants:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hackathon is full")
        participant = Participant(hackathonId=team.hackathonId, userId=currentUser.id, teamId=team.id, contextRole="PARTICIPANT")
        hackathon.currentParticipants += 1
        db.add(participant)
    else:
        participant.teamId = team.id

    db.commit()
    db.refresh(team)
    return team

@router.get("/{id}", response_model=TeamDetailResponse)
def getTeam(id: int, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    participants = db.query(Participant).filter(Participant.teamId == team.id).all()
    members = []
    for p in participants:
        user = db.query(User).filter(User.id == p.userId).first()
        members.append({
            "id": p.id,
            "userId": p.userId,
            "contextRole": p.contextRole,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
    
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        inviteCode=team.inviteCode,
        hackathonId=team.hackathonId,
        creatorId=team.creatorId,
        createdAt=team.createdAt,
        members=members
    )

@router.post("/{id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leaveTeam(id: int, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    participant = db.query(Participant).filter(
        Participant.teamId == team.id,
        Participant.userId == currentUser.id
    ).first()

    if not participant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not a member of this team")

    if team.creatorId == currentUser.id:
        db.query(Participant).filter(Participant.teamId == team.id).update({Participant.teamId: None})
        db.delete(team)
    else:
        participant.teamId = None

    db.commit()
    return None