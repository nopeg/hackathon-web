from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from app.database import getDB
from app.models.userModel import User
from app.models.verificationToken import VerificationToken
from app.schemas.userSchema import UserCreate, UserResponse
from app.schemas.tokenSchema import Token
from app.core.config import settingsInstance
from app.core.security import hashPassword, verifyPassword, createAccessToken, getCurrentUser, decodeToken
from app.core.emailUtils import generateVerificationToken, sendVerificationEmail

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(userIn: UserCreate, request: Request, db: Session = Depends(getDB)):
    if db.query(User).filter(User.username == userIn.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == userIn.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hashPassword(userIn.password)
    newUser = User(
        username=userIn.username,
        email=userIn.email,
        hashedPassword=hashed,
        role=userIn.role,
        isVerified=False,
        isBanned=False
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)

    token = generateVerificationToken(newUser.email)
    expiresAt = datetime.now(timezone.utc) + timedelta(hours=24)
    dbToken = VerificationToken(userEmail=newUser.email, token=token, expiresAt=expiresAt)
    db.add(dbToken)
    db.commit()

    baseUrl = f"{request.headers.get('x-forwarded-proto', 'http')}://{request.headers.get('host', 'localhost')}"
    
    try:
        sendVerificationEmail(newUser.email, token, baseUrl)
    except Exception as e:
        db.delete(newUser)
        db.delete(dbToken)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to send verification email: {str(e)}")

    return newUser

@router.post("/login", response_model=Token)
def login(formData: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDB)):
    user = db.query(User).filter(User.username == formData.username).first()
    if not user or not verifyPassword(formData.password, user.hashedPassword):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.isVerified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your email."
        )
    if user.isBanned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been banned."
        )
    accessToken = createAccessToken(data={"sub": user.username})
    return {"access_token": accessToken, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def getCurrentUserInfo(currentUser: str = Depends(getCurrentUser), db: Session = Depends(getDB)):
    user = db.query(User).filter(User.username == currentUser).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/verifyEmail")
def verifyEmail(token: str, db: Session = Depends(getDB)):
    try:
        payload = decodeToken(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(400, "Invalid token")
        
        dbToken = db.query(VerificationToken).filter(VerificationToken.token == token).first()
        if not dbToken:
            raise HTTPException(400, "Token not found")
        
        expires_at = dbToken.expiresAt
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(400, "Token expired")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        user.isVerified = True
        db.delete(dbToken)
        db.commit()

        accessToken = createAccessToken(data={"sub": user.username})
        return {
            "access_token": accessToken,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))