from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import getDB
from app.models.userModel import User
from app.schemas.userSchema import UserCreate, UserResponse
from app.schemas.tokenSchema import Token
from app.core.config import settingsInstance
from app.core.security import (
    hashPassword, 
    verifyPassword, 
    createAccessToken,
    getCurrentUsername
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(userIn: UserCreate, db: Session = Depends(getDB)):
    dbUsername = db.query(User).filter(User.username == userIn.username).first()
    if dbUsername:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    dbEmail = db.query(User).filter(User.email == userIn.email).first()
    if dbEmail:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashedPassword = hashPassword(userIn.password)
    newUser = User(
        username=userIn.username,
        email=userIn.email,
        hashedPassword=hashedPassword,
        role=userIn.role
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    return newUser

@router.post("/login", response_model=Token)
def login(formData: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDB)):
    user = db.query(User).filter(User.username == formData.username).first()
    if not user or not verifyPassword(formData.password, user.hashedPassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    accessTokenExpires = timedelta(minutes=settingsInstance.accessTokenExpireMinutes)
    accessToken = createAccessToken(
        data={"sub": user.username}, expiresDelta=accessTokenExpires
    )
    return {"accessToken": accessToken, "tokenType": "bearer"}

@router.get("/me", response_model=UserResponse)
def getCurrentUser(username: str = Depends(getCurrentUsername), db: Session = Depends(getDB)):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user