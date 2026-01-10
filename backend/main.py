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

# CORS (Allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IN-MEMORY DB
db = {
    "devices": [],
    "networkOverview": {"avgTrustScore": 0.0, "devicesAtRisk": 0, "activeGateways": 0}
}

# DATA MODELS
class DeviceInteractions(BaseModel):
    device_id: str
    history: List[List[float]] #(300x6)

# ENDPOINTS
@app.get("/api/dashboard")
def get_dashboard_data():
    return db

@app.post("/api/analyze-behaviour")
def analyze_behaviour(data: DeviceInteractions):
    try:
        trust_column = [row[0] for row in data.history]
        
        min_trust = min(trust_column)
        max_trust = max(trust_column)
        last_trust = trust_column[-1] 
        
        trust_range_str = f"{min_trust:.2f} - {max_trust:.2f} | Last: {last_trust:.2f}"
        trust_avg = sum(trust_column) / len(trust_column)

    except Exception as e:
        print(f"ERROR: {e}")
        trust_range_str = "N/A"
        trust_avg = 0.0

    # CNN classification
    class_int = pipeline.predict_trust(data.history)

    if class_int <= 15: 
        status = "Normal"
    elif class_int >= 16:
        status = "At Risk"
    else:
        status = "ERROR"

    existing_device = next((device for device in db["devices"] if device["id"] == data.device_id), None)
    device_entry = {
        "id": data.device_id,
        "trustAvg": round(trust_avg, 3),
        "trustDisplay": trust_range_str,
        "status": status,
        "profile": f"Class {class_int}"
    }

    # Update database
    if existing_device:
        existing_device.update(device_entry)
    else:
        db["devices"].append(device_entry)

    # Avg all devices avg trust
    trust_all_device = [device["trustAvg"] for device in db["devices"]]
    if trust_all_device:
        db["networkOverview"]["avgTrustScore"] = round(sum(trust_all_device) / len(trust_all_device), 2)
    db["networkOverview"]["devicesAtRisk"] = sum(1 for device in db["devices"] if device["status"] == "At Risk")

    return {
        "message": "Analyzed", 
        "device_class_pred": class_int,
        "status": status
    }