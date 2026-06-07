import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import getDB
from app.models.userModel import User
from app.models.hackathonModel import Hackathon
from app.schemas.hackathonSchema import HackathonCreate, HackathonUpdate, HackathonResponse
from app.core.security import getCurrentUser
from app.routers.hackathonRouter import createHackathon, updateHackathon, deleteHackathon

router = APIRouter(prefix="/editor", tags=["editor"])

UPLOAD_DIR = "static/uploads"

def getCurrentUserFromDB(username: str = Depends(getCurrentUser), db: Session = Depends(getDB)) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), currentUser: User = Depends(getCurrentUserFromDB)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    image_url = f"/static/uploads/{filename}"
    return {"url": image_url}

@router.post("/hackathons", response_model=HackathonResponse, status_code=status.HTTP_201_CREATED)
def create_hackathon_editor(hackathonIn: HackathonCreate, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    return createHackathon(hackathonIn, db, currentUser)

@router.put("/hackathons/{id}", response_model=HackathonResponse)
def update_hackathon_editor(id: int, hackathonIn: HackathonUpdate, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    return updateHackathon(id, hackathonIn, db, currentUser)

@router.delete("/hackathons/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hackathon_editor(id: int, db: Session = Depends(getDB), currentUser: User = Depends(getCurrentUserFromDB)):
    return deleteHackathon(id, db, currentUser)