from fastapi import FastAPI

from app.routes.assessments import router as assessments_router
from app.routes.auth import router as auth_router
from app.routes.calculation import router as calculation_router
from app.routes.observations import router as observations_router
from app.routes.patients import router as patients_router
from app.routes.questionnaires import router as questionnaires_router
from app.routes.responses import router as responses_router

app = FastAPI(
    title="AyurEssence API",
    description="Intelligent Ayurvedic Prakriti Assessment Platform",
    version="1.0.0"
)

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


app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(assessments_router)
app.include_router(questionnaires_router)
app.include_router(responses_router)
app.include_router(observations_router)
app.include_router(calculation_router)
