from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from app.routers import auth, hackathon

def create_application() -> FastAPI:
    fast_api_app = FastAPI(title="Hackathon Platform API")

    fast_api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # fast_api_app.include_router(auth.router)
    return fast_api_app

app = create_application()

@app.get("/health")
async def check_health():
    return {"status": "ok"}