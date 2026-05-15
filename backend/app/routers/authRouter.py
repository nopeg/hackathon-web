from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import getDB
from app.models.userModel import User
from app.schemas.userSchema import UserCreate, UserRead
from app.core.security import hashPassword

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def registerUser(userData: UserCreate, db: Session = Depends(getDB)):
    existingUser = db.query(User).filter(
        (User.email == userData.email) | (User.username == userData.username)
    ).first()
    
    if existingUser:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )

    newUser = User(
        email=userData.email,
        username=userData.username,
        hashed_password=hashPassword(userData.password)
    )
    
    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    
    return newUser