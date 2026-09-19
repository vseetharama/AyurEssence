from fastapi import FastAPI

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
