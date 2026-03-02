from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from google import genai  
import os
import json
import re

# Import your pipeline
from trust_engine import TrustModelPipeline

# Initialize Pipeline
pipeline = TrustModelPipeline()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load CNN model and scaler on startup
    success = pipeline.load_resources()
    if success:
        print("✅ Startup: CNN Model and Scaler loaded successfully.")
    else:
        print("❌ Startup: Failed to load CNN or Scaler.")
    yield

app = FastAPI(lifespan=lifespan)

# CORS (Allow frontend requests from Vite/React/Vue)
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
    "networkOverview": {"avgTrustScore": 0.0, "devicesAtRisk": 0, "activeGateways": 0},
    "raw_histories": {} 
}

# DATA MODELS
class DeviceInteractions(BaseModel):
    device_id: str
    history: List[List[float]] 

class ChatMessage(BaseModel):
    role: str 
    parts: str

class ChatRequest(BaseModel):
    device_id: str
    history: List[ChatMessage] = []
    new_message: Optional[str] = None

# --- HELPERS ---

def get_device_data(device_id_input):
    """
    Directly parses the device number from the input string 
    and fetches its 8-row block from the CSV.
    """
    try:
        # 1. Extract ONLY the digits from the string (e.g., "Device-12" -> 12)
        digits = re.findall(r'\d+', str(device_id_input))
        if not digits:
            print(f"❌ Could not find a number in: {device_id_input}")
            return None
        
        device_num = int(digits[0])
        # 1. Get the directory where main.py is (e.g., .../backend)
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 2. Go UP one level and find the CSV (since it's in the parent folder)
        csv_path = os.path.join(base_dir, "..", "Sample Data 21 Devices - 8 Attr.csv")

        # 3. Load the CSV using the absolute path we just built
        try:
            df = pd.read_csv(csv_path, header=None)
            print(f"✅ Successfully loaded: {csv_path}")
        except FileNotFoundError:
            print(f"❌ Still can't find the file at: {csv_path}")
            # Fallback: if '..' is wrong, try looking in the current folder
            df = pd.read_csv("Sample Data 21 Devices - 8 Attr.csv", header=None)
        
        # 3. Apply the x*8-8 logic to find the starting row
        start_row = (device_num * 8) - 8
        
        # 4. Extract the 8 rows for this device
        # Rows: 0:Delay, 1:Trust, 2:History, 3:Throughput, 4:Enc, 5:Auth, 6:Battery, 7:Age
        block = df.iloc[start_row : start_row + 8, :50]
        
        def calc_stats(row_idx):
           # 1. Clean the data
            data = pd.to_numeric(block.iloc[row_idx], errors='coerce').dropna().values
            
            # Safety check for small datasets
            if len(data) < 3:
                val = float(np.mean(data)) if len(data) > 0 else 0.0
                return {"mean": round(val, 3), "min": round(val, 3), "max": round(val, 3), "std": 0.0}

            # 2. Get 2nd Min and 2nd Max for the boundaries
            # np.partition(data, 1) puts 1st min at [0], 2nd min at [1]
            # np.partition(data, -2) puts 2nd max at [-2], 1st max at [-1]
            part_min = np.partition(data, 1)
            part_max = np.partition(data, -2)
            
            second_min = float(part_min[1])
            second_max = float(part_max[-2])

            # 3. Calculate Trimmed Mean
            # We sort the data and slice off the first and last elements [1:-1]
            # This removes the outliers from the average calculation
            trimmed_data = np.sort(data)[1:-1]
            trimmed_mean = float(np.mean(trimmed_data))

            return {
                "mean": round(trimmed_mean, 3), # Now resistant to outliers
                "min": round(second_min, 3),    # 2nd smallest
                "max": round(second_max, 3),    # 2nd largest
                "std": round(float(np.std(data)), 4)
            }
        

        # 5. Build the context object for the LLM
        return {
            "device_id": device_num,
            "metadata": {
                "DeviceSensorAgeMonths": int(df.iloc[start_row + 7, 0])
            },
            "InteractionStatistics": {
                "NetworkDelay": calc_stats(0),
                "TrustValue": calc_stats(1),
                "InteractionHistory": calc_stats(2),
                "NetworkThroughput": calc_stats(3),
                "SecurityStrengthEncryption": calc_stats(4),
                "SecurityStrengthMessageAuthentication": calc_stats(5),
                "DeviceBatteryPercentage": calc_stats(6)
            }
        }
    except Exception as e:
        print(f"❌ Error parsing {device_id_input}: {e}")
        return None
    
def calculate_detailed_stats(data_row):
    """Calculates the 6-point statistical summary: mean, min, 10th percentile, 90th percentile, max, std."""
    data = pd.to_numeric(data_row, errors='coerce').dropna()
    if data.empty:
        return {"mean": 0, "min": 0, "max": 0, "std": 0}
    return {
        
        "min": round(float(np.partition(data, 1)[1]), 3),
        "mean": round(float(np.mean(data)), 3),
        #"min2": round(float(np.percentile(data, 10)), 3),
        #"max2": round(float(np.percentile(data, 90)), 3),
        "max": round(float(np.max(data)), 3),
        "std": round(float(np.std(data)), 4)
    }

def get_device_context_from_spreadsheet(device_id_str: str):
    """
    Generic parser for ANY device. 
    Uses x*8-8 logic to find the data block in the CSV.
    """
    try:
        # 1. Extract the number from the string (e.g., 'Device-14' -> 14)
        match = re.search(r'\d+', str(device_id_str))
        if not match: return None
        x = int(match.group())
        
        # 2. Load the spreadsheet
        csv_path = "Sample Data 21 Devices - 8 Attr.csv"
        df = pd.read_csv(csv_path, header=None)
        
        # 3. Apply the x*8-8 logic
        start_row = (x * 8) - 8
        
        if start_row < 0 or start_row + 7 >= len(df):
            return None
            
        # Slice the 8 rows and first 50 columns
        block = df.iloc[start_row : start_row + 8, :50]
        
        # 4. Build the JSON structure for context_text
        return {
            "device_id": x,
            "metadata": {
                "snapshot_time": "09:10:00-09:10:50",
                "window_size": 50,
                "DeviceSensorAgeMonths": int(df.iloc[start_row + 7, 0])
            },
            "InteractionStatistics": {
                "TrustValue": calculate_detailed_stats(block.iloc[1]),
                "InteractionHistory": calculate_detailed_stats(block.iloc[2]),
                "NetworkThroughput": calculate_detailed_stats(block.iloc[3]),
                "NetworkDelay": calculate_detailed_stats(block.iloc[0]),
                "SecurityStrengthEncryption": calculate_detailed_stats(block.iloc[4]),
                "SecurityStrengthMessageAuthentication": calculate_detailed_stats(block.iloc[5]),
                "DeviceBatteryPercentage": calculate_detailed_stats(block.iloc[6])
            }
        }
    except Exception as e:
        print(f"Error extracting data for {device_id_str}: {e}")
        return None

# --- ENDPOINTS ---

@app.get("/api/dashboard")
def get_dashboard_data():
    return {
        "devices": db["devices"],
        "networkOverview": db["networkOverview"]
    }

@app.post("/api/analyze-behaviour")
def analyze_behaviour(data: DeviceInteractions):
    try:
        db["raw_histories"][data.device_id] = data.history
        trust_column = [row[0] for row in data.history]
        trust_avg = sum(trust_column) / len(trust_column)
        trust_range_str = f"{min(trust_column):.2f} - {max(trust_column):.2f} | Last: {trust_column[-1]:.2f}"
    except Exception as e:
        trust_avg, trust_range_str = 0.0, "N/A"

    class_int = pipeline.predict_trust(data.history)
    status = "At Risk" if class_int > 15 else ("Normal" if trust_avg > 0.50 else "Warning")

    device_entry = {
        "id": data.device_id, "trustAvg": round(trust_avg, 3), "trustDisplay": trust_range_str,
        "status": status, "profile": f"Class {class_int}"
    }

    # Update state
    existing = next((d for d in db["devices"] if d["id"] == data.device_id), None)
    if existing: existing.update(device_entry)
    else: db["devices"].append(device_entry)

    # Global Stats
    trust_all = [d["trustAvg"] for d in db["devices"]]
    if trust_all: db["networkOverview"]["avgTrustScore"] = round(sum(trust_all) / len(trust_all), 2)
    db["networkOverview"]["devicesAtRisk"] = sum(1 for d in db["devices"] if d["status"] == "At Risk")

    return {"message": "Analysis Complete", "device_class_pred": class_int, "status": status}

@app.post("/api/llm-analyze")
async def llm_analyze(request: ChatRequest):
    api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY").strip()
    client = genai.Client(api_key=api_key)
    
    # DYNAMIC INJECTION: Works for any device passed from the frontend
    stats_data = get_device_data(request.device_id)
    
    if stats_data:
        # Convert the dictionary to a pretty JSON string for the prompt
        context_text = json.dumps(stats_data, indent=2)
    else:
        context_text = f"Device {request.device_id} data not found."
    
    if not request.history:
        # context_text is now dynamically generated JSON for the chosen device
        context_text = json.dumps(stats_data, indent=2) if stats_data else f"Device {request.device_id} context unavailable."
        
        prompt = (
            f"""You are an IoT Device Health and Security Diagnostic Language Model. Analyze IoT device snapshots using ONLY the providedinteraction statistics and metadata, with NO predefined classes or
            external labels. Your responsibilities are to identify issues, explainthem, and recommend actions using concise, operator-friendlylanguage.​

            MANDATORY RULES: ​

            Use ONLY provided input values.​
            - Do NOT account for outliers
            - Do NOT invent behavior beyond statistical evidence.​
            - Explicitly state uncertainty if evidence is limited. ​
            - EACH textual output field MUST be EXACTLY ONE sentence. ​
            - Remember analysed device input data if user wants the raw data
            - Output MUST be valid JSON only.​

            PRIORITY HEURISTICS: ​
            - Trust is an anaylytical combination of all attributes and is the main attribute to determine device safety
            - If sensor_age > 72 months, consider sensor aging as a minor contributing factor. ​
            - If battery power ever drops below 20%, treat power-related degradation as high priority. ​
            - Low mean indicates baseline weakness, low min indicates worst-case risk, and high std indicates instability. ​
            - Strong mean with sharp drops suggests intermittent degradation. ​
            - SecurityStrengthMessageAuthentication & SecurityStrengthEncryption are represented as industry standard at 256, shown in stages as 128, 64, …, 0​

                OUTPUT FORMAT (MANDATORY JSON ONLY): ​
                {{
                "device_id": <int>, ​
                "summary": "<2–4 word status>",​
                "observed_issues": ["<one sentence highlighting specific metric issues>"], ​
                "evidence": ["<one sentence citing specific values from the data>"], ​
                "risk_assessment": "<one sentence evaluating the overall risk level>", ​
                "recommended_actions": ["<one sentence recommendation>"], ​
                "risk": <0.0–1.0>,​
                "confidence": <0.0–1.0>​
                }}​ Device to be analysed: \n{context_text}\n\n"""
        )
    else:
        prompt = request.new_message

    contents = [{"role": "user" if m.role == "user" else "model", "parts": [{"text": m.parts}]} for m in request.history]
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    try:
        response = client.models.generate_content(model="gemini-3.1-pro-preview", contents=contents)
        return {
            "response": response.text,
            "history": request.history + [{"role": "user", "parts": prompt}, {"role": "model", "parts": response.text}]
        }
    except Exception as e:
        return {"response": "⚠️ AI Analysis is currently unavailable.", "history": request.history}

@app.get("/api/diagnose/{device_id}")
async def get_ai_diagnostic(device_id: str):
    """Pipeline: Turns spreadsheet data into detailed statistics for diagnostic."""
    stats_payload = get_device_context_from_spreadsheet(device_id)
    if not stats_payload:
        raise HTTPException(status_code=404, detail=f"Data for device {device_id} not found.")

    try:
        report = await pipeline.get_llm_diagnostic(stats_payload)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic Error: {str(e)}")