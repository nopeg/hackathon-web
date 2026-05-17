from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import authRouter

app = FastAPI(title="Hackathon Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authRouter.router)

@app.get("/health", tags=["default"])
def checkHealth():
    return {"status": "ok"} 