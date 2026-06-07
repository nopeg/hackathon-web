from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import getDB
from app.models.userModel import User, UserRole
from app.models.hackathonModel import Hackathon
from app.schemas.userSchema import UserResponse
from app.core.security import getCurrentUserWithRole

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(currentUser: User):
    if currentUser.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

def require_moderator(currentUser: User):
    if currentUser.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator access required")

@router.get("/users", response_model=List[UserResponse])
def get_all_users(currentUser: User = Depends(getCurrentUserWithRole), db: Session = Depends(getDB)):
    require_admin(currentUser)
    return db.query(User).all()

@router.post("/users/{user_id}/ban")
def ban_user(user_id: int, currentUser: User = Depends(getCurrentUserWithRole), db: Session = Depends(getDB)):
    require_moderator(currentUser)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot ban an admin")
    user.isBanned = True
    db.commit()
    return {"message": f"User {user.username} banned successfully"}

@router.post("/users/{user_id}/unban")
def unban_user(user_id: int, currentUser: User = Depends(getCurrentUserWithRole), db: Session = Depends(getDB)):
    require_moderator(currentUser)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.isBanned = False
    db.commit()
    return {"message": f"User {user.username} unbanned successfully"}

@router.delete("/hackathons/{hackathon_id}")
def delete_any_hackathon(hackathon_id: int, currentUser: User = Depends(getCurrentUserWithRole), db: Session = Depends(getDB)):
    require_moderator(currentUser)
    hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    db.delete(hackathon)
    db.commit()
    return {"message": f"Hackathon '{hackathon.title}' deleted successfully"}