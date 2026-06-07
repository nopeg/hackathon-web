from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
import os
from app.routers import authRouter, hackathonRouter, teamRouter, editorRouter, userRouter, adminRouter
from app.core.security import createAccessToken, verifyPassword
from app.database import getDB
from sqlalchemy.orm import Session
from app.models.userModel import User

app = FastAPI(title="Hackathon Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authRouter.router)
app.include_router(hackathonRouter.router)
app.include_router(teamRouter.router)
app.include_router(editorRouter.router)
app.include_router(userRouter.router)
app.include_router(adminRouter.router)

@app.post("/auth/token")
def login_alias(formData: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDB)):
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

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/static/uploads/{filename}")
async def get_image(filename: str):
    file_path = f"static/uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    if filename.lower().endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif filename.lower().endswith(".png"):
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"
    return FileResponse(file_path, media_type=media_type, headers={"Content-Disposition": f"inline; filename={filename}"})

@app.get("/health", tags=["health"])
def healthCheck():
    return {"status": "ok"}