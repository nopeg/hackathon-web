from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settingsInstance
from app.database import getDB
from app.models.userModel import User

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hashPassword(password: str) -> str:
    passwordBytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(passwordBytes, salt)
    return hashedPassword.decode('utf-8')

def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    passwordBytes = plainPassword.encode('utf-8')
    hashedBytes = hashedPassword.encode('utf-8')
    return bcrypt.checkpw(passwordBytes, hashedBytes)

def createAccessToken(data: dict, expiresDelta: Optional[timedelta] = None) -> str:
    toEncode = data.copy()
    if expiresDelta:
        expire = datetime.now(timezone.utc) + expiresDelta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settingsInstance.accessTokenExpireMinutes)
    toEncode.update({"exp": expire})
    encodedJwt = jwt.encode(toEncode, settingsInstance.secretKey, algorithm=settingsInstance.algorithm)
    return encodedJwt

def decodeToken(token: str):
    return jwt.decode(token, settingsInstance.secretKey, algorithms=[settingsInstance.algorithm])

def getCurrentUser(token: str = Depends(oauth2Scheme), db: Session = Depends(getDB)) -> str:
    credentialsException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodeToken(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentialsException
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.isVerified:
            raise credentialsException
        return username
    except JWTError:
        raise credentialsException