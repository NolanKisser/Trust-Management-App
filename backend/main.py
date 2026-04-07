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
from datetime import datetime, timedelta, timezone
from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import PromptInjection as InputPromptInjection
from llm_guard.input_scanners import Toxicity as InputToxicity
from llm_guard.output_scanners import Toxicity as OutputToxicity

# Import your pipeline
from trust_engine import TrustModelPipeline

# Initialize Pipeline
pipeline = TrustModelPipeline()
AI_ENGINE_MODEL = "gemini-3.1-pro-preview"
ATTRIBUTE_INDEX_MAP = {
    "networkDelay": 0,
    "interactionHistory": 2,
    "networkThroughput": 3,
    "securityEncryption": 4,
    "securityAuthentication": 5,
    "batteryPercentage": 6,
    "sensorAgeMonths": 7
}

# Mean trust above this => Normal when CNN class <= 15; at or below => Warning (see analyze_behaviour).
TRUST_NORMAL_MIN = 0.52

# Map dashboard device id -> 1-based block index in "Sample Data 21 Devices - 8 Attr.csv"
SPREADSHEET_DEVICE_BLOCK = {
    "Device-3": 21,
    "Device-5": 11,
}

# Spreadsheet blocks whose telemetry matches known attack / on-off style profiles (LLM + diagnostics)
SPREADSHEET_ATTACK_PROFILE_BLOCKS = frozenset({4, 21})


def spreadsheet_block_index(device_id_str: str) -> Optional[int]:
    """Return 1-based device block index in CSV (rows (n-1)*8 .. n*8-1)."""
    key = str(device_id_str).strip()
    if key in SPREADSHEET_DEVICE_BLOCK:
        return SPREADSHEET_DEVICE_BLOCK[key]
    digits = re.findall(r"\d+", key)
    if not digits:
        return None
    return int(digits[0])


def dashboard_device_number(device_id_str: str) -> Optional[int]:
    """UI device index from id string (e.g. Device-3 -> 3), independent of spreadsheet remap."""
    digits = re.findall(r"\d+", str(device_id_str).strip())
    return int(digits[0]) if digits else None


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
    "raw_histories": {},
    "device_timeline_meta": {}
}

# LLM Guard scanners (initialized once at startup time for reuse).
input_scanners = [
    InputToxicity(threshold=0.7),
    InputPromptInjection(threshold=0.8)
]
output_scanners = [
    OutputToxicity(threshold=0.7)
]
output_jailbreak_scanner = InputPromptInjection(threshold=0.8)

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

def get_device_data(device_id_input, x):
    """
    Fetches the 8-row block from the CSV using spreadsheet_block_index (supports
    e.g. Device-5 -> block 15 when the UI shows Device-5 but data is from profile 15).
    """
    try:
        block_idx = spreadsheet_block_index(device_id_input)
        if block_idx is None:
            print(f"❌ Could not find a number in: {device_id_input}")
            return None

        logical_id = dashboard_device_number(device_id_input)
        if logical_id is None:
            logical_id = block_idx

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
        start_row = (block_idx * 8) - 8
        
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
        

        # 5. Build the context object for the LLM (device_id = dashboard slot; data_profile_block = CSV block)
        attack_flag = (str(x).strip() == "Device-4") or (block_idx in SPREADSHEET_ATTACK_PROFILE_BLOCKS)
        return {
            "device_id": logical_id,
            "device_label": str(device_id_input).strip(),
            "data_profile_block": block_idx,
            "On-Off-Attack": attack_flag,
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
        block_idx = spreadsheet_block_index(device_id_str)
        if block_idx is None:
            return None

        logical_id = dashboard_device_number(device_id_str)
        if logical_id is None:
            logical_id = block_idx

        # 2. Load the spreadsheet (project root, same as get_device_data)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "..", "Sample Data 21 Devices - 8 Attr.csv")
        if not os.path.isfile(csv_path):
            csv_path = "Sample Data 21 Devices - 8 Attr.csv"
        df = pd.read_csv(csv_path, header=None)
        
        # 3. Apply the x*8-8 logic
        start_row = (block_idx * 8) - 8
        
        if start_row < 0 or start_row + 7 >= len(df):
            return None
            
        # Slice the 8 rows and first 50 columns
        block = df.iloc[start_row : start_row + 8, :50]
        
        # 4. Build the JSON structure for context_text
        attack_flag = (str(device_id_str).strip() == "Device-4") or (block_idx in SPREADSHEET_ATTACK_PROFILE_BLOCKS)
        return {
            "device_id": logical_id,
            "device_label": str(device_id_str).strip(),
            "data_profile_block": block_idx,
            "On-Off-Attack": attack_flag,
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
        "networkOverview": db["networkOverview"],
        "aiEngineModel": AI_ENGINE_MODEL
    }

@app.post("/api/analyze-behaviour")
def analyze_behaviour(data: DeviceInteractions):
    try:
        db["raw_histories"][data.device_id] = data.history
        trust_column = [float(row[1]) for row in data.history]
        trust_avg = sum(trust_column) / len(trust_column)
        trust_current = trust_column[-1]
        trust_range_str = f"{min(trust_column):.2f} - {max(trust_column):.2f} | Current: {trust_current:.2f}"
    except Exception as e:
        trust_avg, trust_current, trust_range_str, trust_column = 0.0, 0.0, "N/A", []

    now_utc = datetime.now(timezone.utc)
    timeline_meta = db["device_timeline_meta"].get(data.device_id)
    if not timeline_meta:
        timeline_meta = {"initiated_at": now_utc.isoformat()}
        db["device_timeline_meta"][data.device_id] = timeline_meta

    initiated_at = datetime.fromisoformat(timeline_meta["initiated_at"])
    end_time = initiated_at + timedelta(seconds=max(0, len(trust_column) - 1))
    trust_timestamps = [
        (initiated_at + timedelta(seconds=index)).isoformat()
        for index in range(len(trust_column))
    ]
    attribute_series = {key: [] for key in ATTRIBUTE_INDEX_MAP.keys()}
    for row in data.history:
        for attribute_key, attribute_index in ATTRIBUTE_INDEX_MAP.items():
            if len(row) <= attribute_index:
                continue
            try:
                attribute_series[attribute_key].append(round(float(row[attribute_index]), 3))
            except (TypeError, ValueError):
                continue

    class_int = pipeline.predict_trust(data.history)
    status = "At Risk" if class_int > 15 else ("Normal" if trust_avg > TRUST_NORMAL_MIN else "Warning")

    device_entry = {
        "id": data.device_id, "trustAvg": round(trust_avg, 3), "trustCurrent": round(trust_current, 3), "trustDisplay": trust_range_str,
        "status": status, "profile": f"Class {class_int}",
        "trustSeries": [round(value, 3) for value in trust_column],
        "attributeSeries": attribute_series,
        "trustTimestamps": trust_timestamps,
        "initiatedAt": timeline_meta["initiated_at"],
        "graphEndAt": end_time.isoformat(),
        "timelineLength": len(trust_column),
        "lastAnalyzedAt": now_utc.isoformat()
    }

    # Update state
    existing = next((d for d in db["devices"] if d["id"] == data.device_id), None)
    if existing: existing.update(device_entry)
    else: db["devices"].append(device_entry)

    # Global Stats (average based on each device's current/latest trust)
    trust_all_current = [d.get("trustCurrent", d.get("trustAvg", 0.0)) for d in db["devices"]]
    if trust_all_current:
        db["networkOverview"]["avgTrustScore"] = round(sum(trust_all_current) / len(trust_all_current), 2)
    db["networkOverview"]["devicesAtRisk"] = sum(1 for d in db["devices"] if d["status"] == "At Risk")

    return {"message": "Analysis Complete", "device_class_pred": class_int, "status": status}

@app.post("/api/llm-analyze")
async def llm_analyze(request: ChatRequest):
    api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY").strip()
    client = genai.Client(api_key=api_key)
    
    # DYNAMIC INJECTION: Works for any device passed from the frontend
    stats_data = get_device_data(request.device_id, request.device_id)
    
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
            - Output MUST be valid JSON only.​

            PRIORITY HEURISTICS: ​
            - If On-Off-Attack is True, notify the user about TMS Neural Network detection of on-off attack patterns. ​
            - Trust is an anaylytical combination of all attributes and is the main attribute to determine device safety but On-Off-Attack is a critical red flag and trust is as reliable. Reccommend immediate investigation and take a look at other attributes to make reason. ​
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
        prompt = (
            f"""You are an IoT Device Health and Security Diagnostic Language Model. The user already received a structured JSON diagnostic in an earlier turn; this message is a FOLLOW-UP only.

            FOLLOW-UP OUTPUT FORMAT (MANDATORY — different from the initial report):
            - Answer in plain natural language only. Do NOT output JSON, YAML, or key-value blocks.
            - Do NOT use field names like device_id, summary, observed_issues, evidence, risk_assessment, recommended_actions, risk, or confidence.
            - Do NOT wrap the answer in markdown code fences unless the user explicitly asks for code.
            - Match the user's request shape: e.g. if they ask for a 3-sentence summary, respond with exactly three sentences in one short paragraph; if they ask a yes/no question, lead with yes or no then brief reasoning.
            - You may use short paragraphs or bullet points when listing multiple items; keep tone concise and operator-friendly.

            CONTENT RULES:
            - Use ONLY the provided device statistics and chat context. Do not invent metrics.
            - Do NOT rely on outlier removal; cite ranges/means from the data when relevant.
            - State uncertainty when evidence is thin.

            PRIORITY HEURISTICS (same as initial analysis):
            - Trust combines attributes; On-Off-Attack True is a critical red flag if present in data.
            - If sensor age > 72 months, mention aging as a possible minor factor.
            - Battery below 20% in the data is high priority for power-related concern.
            - SecurityStrengthMessageAuthentication & SecurityStrengthEncryption use industry stages 256, 128, 64, …, 0.

            Device data (reference):\n{context_text}\n\nUser follow-up question:\n{request.new_message}\n"""
        )

    # 1) Input sanitization + prompt injection protection before Gemini call.
    sanitized_prompt, input_valid_map, input_score_map = scan_prompt(input_scanners, prompt)
    if any(not is_valid for is_valid in input_valid_map.values()):
        return {
            "response": "⚠️ Request blocked by security checks (input toxicity or prompt injection).",
            "history": request.history,
            "guard": {
                "stage": "input",
                "valid": input_valid_map,
                "score": input_score_map
            }
        }

    contents = [{"role": "user" if m.role == "user" else "model", "parts": [{"text": m.parts}]} for m in request.history]
    contents.append({"role": "user", "parts": [{"text": sanitized_prompt}]})

    try:
        response = client.models.generate_content(model=AI_ENGINE_MODEL, contents=contents)
        response_text = response.text or ""

        # 2) Output toxicity detection.
        sanitized_output, output_valid_map, output_score_map = scan_output(
            output_scanners,
            sanitized_prompt,
            response_text
        )
        if any(not is_valid for is_valid in output_valid_map.values()):
            return {
                "response": "⚠️ Model output blocked by security checks.",
                "history": request.history + [{"role": "user", "parts": sanitized_prompt}],
                "guard": {
                    "stage": "output_toxicity",
                    "valid": output_valid_map,
                    "score": output_score_map
                }
            }

        # 3) Output jailbreak detection (model text attempting policy bypass).
        _, is_output_jailbreak_safe, output_jailbreak_score = output_jailbreak_scanner.scan(sanitized_output)
        if not is_output_jailbreak_safe:
            return {
                "response": "⚠️ Model output blocked by security checks (jailbreak pattern detected).",
                "history": request.history + [{"role": "user", "parts": sanitized_prompt}],
                "guard": {
                    "stage": "output_jailbreak",
                    "valid": {"PromptInjection": is_output_jailbreak_safe},
                    "score": {"PromptInjection": output_jailbreak_score}
                }
            }

        return {
            "response": sanitized_output,
            "history": request.history + [{"role": "user", "parts": sanitized_prompt}, {"role": "model", "parts": sanitized_output}]
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