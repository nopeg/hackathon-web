from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.routers import authRouter, hackathonRouter, teamRouter, editorRouter, userRouter

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