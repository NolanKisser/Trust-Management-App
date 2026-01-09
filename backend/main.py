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
    "devices": [], # populated by Auto-Discovery
    "networkOverview": {"avgTrustScore": 0.0, "devicesAtRisk": 0, "activeGateways": 5}
}

# --- Data Models ---
class InteractionBatch(BaseModel):
    device_id: str
    history: List[List[float]] # (300x6)

# --- Endpoints ---
@app.get("/api/dashboard")
def get_dashboard_data():
    return db

@app.post("/api/analyze-trust")
def analyze_trust(data: InteractionBatch):
    try:
        trust_column = [row[0] for row in data.history]
        
        min_val = min(trust_column)
        max_val = max(trust_column)
        last_val = trust_column[-1] 
        
        range_string = f"{min_val:.2f} - {max_val:.2f} | Last: {last_val:.2f}"

        current_batch_average = sum(trust_column) / len(trust_column)

    except Exception as e:
        print(f"Error processing raw data: {e}")
        range_string = "N/A"
        current_batch_average = 0.0

    # CNN Classification
    result = pipeline.predict_trust(data.history)
    class_integer = result["device_class_pred"]

    # Update database
    status = "Normal"
    if class_integer >= 16: status = "At Risk"

    existing_device = next((d for d in db["devices"] if d["id"] == data.device_id), None)
    
    device_entry = {
        "id": data.device_id,
        "trustScore": round(current_batch_average, 3),
        "displayRange": range_string,
        "status": status,
        "profile": f"Class {class_integer}",
        "lastSeen": "Just now"
    }

    if existing_device:
        existing_device.update(device_entry)
    else:
        db["devices"].append(device_entry)

    # Average of the current device scores
    all_device_scores = [d["trustScore"] for d in db["devices"]]
    if all_device_scores:
        db["networkOverview"]["avgTrustScore"] = round(sum(all_device_scores) / len(all_device_scores), 2)
    db["networkOverview"]["devicesAtRisk"] = sum(1 for d in db["devices"] if d["status"] == "At Risk")

    return {"message": "Analyzed", "device_class_pred": class_integer}