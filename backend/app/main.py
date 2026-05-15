from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def createApplication() -> FastAPI:
    fastApiApp = FastAPI(title="Hackathon Platform API")

    fastApiApp.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return fastApiApp

appInstance = createApplication()

@appInstance.get("/health")
async def checkHealth():
    return {"status": "ok"}