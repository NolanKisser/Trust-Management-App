import numpy as np
import tensorflow as tf
import joblib
import os
import json
from google import genai  # Migrated to new SDK

class TrustModelPipeline:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = "CNNv2_Filters64-128-256-Kernels20-15-5-Swish_E500-Best.keras"
        self.scaler_path = "scaler.pkl"
        
        # Initialize the new GenAI Client
        self.api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY").strip()
        self.client = genai.Client(api_key=self.api_key)

    def load_resources(self) -> bool:
        """Load CNN and scaler for behavioural classification."""
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path, compile=False)
                print(f"✅ Loaded CNN model: {self.model_path}")
            except Exception as e:
                print(f"❌ ERROR loading CNN: {e}")
                return False
        else:
            print(f"❌ ERROR: Model file not found at {self.model_path}")
            return False

        if os.path.exists(self.scaler_path):
            try:
                self.scaler = joblib.load(self.scaler_path)
                print(f"✅ Loaded Scaler: {self.scaler_path}")
            except Exception as e:
                print(f"❌ ERROR loading scaler: {e}")
                return False
        else:
            print(f"❌ ERROR: Scaler file not found at {self.scaler_path}")
            return False

        return True

    def predict_trust(self, interactions: list) -> int:
        """Expected input shape: (300, 8). Returns 1-indexed class."""
        if not self.model or not self.scaler:
            return -1
        try:
            X_raw = np.array(interactions)
            if X_raw.shape != (300, 8): 
                print(f"⚠️ Shape Mismatch: Expected (300, 8), got {X_raw.shape}")
                return -1
            X_scaled = self.scaler.transform(X_raw) 
            X_input = X_scaled.reshape(1, 300, 8) 
            preds = self.model.predict(X_input, verbose=0)[0]
            return int(np.argmax(preds) + 1)
        except Exception as e:
            print(f"❌ Prediction Logic Error: {e}")
            return -1

    async def get_llm_diagnostic(self, data_payload: dict) -> dict:
        """Sends full statistical nested JSON to Gemini for a structured security diagnostic."""
        try:
            model_id = "gemini-2.5-flash"
            
            # The prompt is now configured to handle the complex nested structure
            # and specifically addresses attributes like sensor age and battery.
            prompt = f"""
                You are an IoT Device Health and Security Diagnostic Model. 
                Analyze the IoT device snapshots using ONLY the provided interaction statistics and metadata.

                MANDATORY RULES: ​
                - Use ONLY provided input values from 'metadata' and 'InteractionStatistics'.​
                - Ignore any external labels. Identify issues based on statistical evidence.
                - EACH textual output field MUST be EXACTLY ONE sentence. ​
                - Output MUST be valid JSON only.​

                PRIORITY HEURISTICS: ​
                - If 'DeviceSensorAgeMonths' > 24, consider sensor aging a significant contributing factor. ​
                - If 'DeviceBatteryPercentage' mean < 20%, treat power-related degradation as high priority. ​
                - Low mean or high 'std' (standard deviation) indicates instability or weakness. ​
                - SecurityStrength fields represent industry standards; 256 being the highest and 0 indicate no protection. Number inbetween can be scaled 0-100

                OUTPUT FORMAT (MANDATORY JSON ONLY): ​
                {{
                "device_id": {data_payload.get('device_id', 0)}, ​
                "summary": "<2–4 word status>",​
                "observed_issues": ["<one sentence highlighting specific metric issues>"], ​
                "evidence": ["<one sentence citing specific values from the data>"], ​
                "risk_assessment": "<one sentence evaluating the overall risk level>", ​
                "recommended_actions": ["<one sentence recommendation>"], ​
                "risk": <0.0–1.0>,​
                "confidence": <0.0–1.0>​
                }}​

                INPUT DATA:
                {json.dumps(data_payload, indent=2)}
            """

            # 1. GENERATE CONTENT
            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            
            # 2. SAFE TEXT EXTRACTION
            if not response or not hasattr(response, 'text') or not response.text:
                 raise ValueError("Gemini returned an empty or malformed response object.")

            clean_text = response.text.strip()
            
            # 3. STRIP MARKDOWN WRAPPERS
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif clean_text.startswith("```"):
                clean_text = clean_text.replace("```", "").strip()
            
            return json.loads(clean_text)

        except Exception as e:
            print(f"❌ [DEBUG] LLM DIAGNOSTIC FAILED: {str(e)}")
            
            return {
                "device_id": data_payload.get("device_id", "Unknown"),
                "summary": "AI Diagnostics Offline",
                "observed_issues": ["The AI engine encountered a processing error."],
                "evidence": [f"Technical detail: {str(e)}"],
                "risk_assessment": "Indeterminate risk status due to AI connection error.",
                "recommended_actions": ["Manual review of device logs required."],
                "risk": 0.5,
                "confidence": 0.0
            }