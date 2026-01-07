from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
from trust_engine import TrustModelPipeline

pipeline = TrustModelPipeline()

@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline.load_resources()
    yield

app = FastAPI(lifespan=lifespan)

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database (In-Memory) ---
db = {
    "devices": [], # Will be populated by Auto-Discovery
    "networkOverview": {"avgTrustScore": 0.0, "devicesAtRisk": 0, "activeGateways": 5}
}

# --- Data Models ---
class InteractionBatch(BaseModel):
    device_id: str
    history: List[List[float]] # Matrix of 300x6

# --- Endpoints ---
@app.get("/api/dashboard")
def get_dashboard_data():
    return db

@app.post("/api/analyze-trust")
def analyze_trust(data: InteractionBatch):
    # 1. Run ML Pipeline
    new_score = pipeline.predict_trust(data.history)
    
    # 2. Determine Status
    status = "Normal"
    if new_score < 0.5: status = "At Risk"
    elif new_score < 0.8: status = "Warning"

    # 3. Update or Create Device
    device = next((d for d in db["devices"] if d["id"] == data.device_id), None)
    if device:
        device["trustScore"] = new_score
        device["status"] = status
    else:
        db["devices"].append({
            "id": data.device_id,
            "trustScore": new_score,
            "status": status,
            "lastSeen": "Just now",
            "profile": "Auto-Detected"
        })

    # 4. Update Overview Stats
    scores = [d["trustScore"] for d in db["devices"]]
    if scores:
        db["networkOverview"]["avgTrustScore"] = round(sum(scores) / len(scores), 2)
    db["networkOverview"]["devicesAtRisk"] = sum(1 for d in db["devices"] if d["status"] == "At Risk")

    return {"message": "Analyzed", "score": new_score, "status": status}