from fastapi import FastAPI

from app.database.connection import Base, engine
from app.routes.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AyurEssence API",
    description="Intelligent Ayurvedic Prakriti Assessment Platform",
    version="1.0.0"
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "AyurEssence Backend API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }