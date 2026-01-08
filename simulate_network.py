import pandas as pd
import requests
import time
import numpy as np

# --- CONFIGURATION ---
FILENAME = "Sample Data 5 devices - Sheet1.csv"
API_URL = "http://localhost:8000/api/analyze-trust"
NUM_DEVICES = 5
NUM_FEATURES = 6
# ---------------------

def main():
    print(f"Loading {FILENAME}...")
    try:
        # Read CSV without header. 
        # We will drop rows that contain text (headers/subtitles) to get just the numbers.
        df = pd.read_csv(FILENAME, header=None)
        
        # Convert all data to numeric, turning text (like "SIA", "Trust") into NaN
        df = df.apply(pd.to_numeric, errors='coerce')
        
        # Drop rows that were headers (NaNs)
        df = df.dropna()
        
        print(f"Cleaned Data Shape: {df.shape}")
        
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # LOGIC:
    # After cleaning, we should have 30 rows total (6 features * 5 devices).
    # Row 0 = Device 1 Trust
    # Row 1 = Device 2 Trust
    # ...
    # Row 5 = Device 1 SIA
    # Row 6 = Device 2 SIA
    
    expected_rows = NUM_DEVICES * NUM_FEATURES
    if df.shape[0] != expected_rows:
        print(f"Warning: Expected {expected_rows} rows (6 features * 5 devices), but found {df.shape[0]}. Check file formatting.")

    # Process each device
    for i in range(NUM_DEVICES):
        device_id = f"Device-{i+1}"
        
        try:
            # Read rows in steps of "X" + ("n" * 5) to collect all "n" features for device "X"
            indices = [i + (f * NUM_DEVICES) for f in range(NUM_FEATURES)]
            
            # Extract these rows
            device_features_df = df.iloc[indices, :]
            
            # Currently Shape is (6, 300).
            # The Model needs (300, 6). So we Transpose (.T) it.
            device_history_matrix = device_features_df.T.values
            
            # Ensure we only send the first 300 columns/interactions
            if device_history_matrix.shape[0] > 300:
                 device_history_matrix = device_history_matrix[:300, :]

            # Convert to Python list for JSON
            history = device_history_matrix.tolist()

            # Create Payload
            payload = {
                "device_id": device_id,
                "history": history
            }

            # Send to Backend
            print(f"Sending {device_id}...", end=" ")
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Score: {result['score']} | Status: {result['status']}")
            else:
                print(f"Failed: {response.text}")
                
        except Exception as e:
            print(f"Error processing {device_id}: {e}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()