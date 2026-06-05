from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import authRouter, hackathonRouter, teamRouter

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

@app.get("/health", tags=["health"])
def healthCheck():
    return {"status": "ok"}