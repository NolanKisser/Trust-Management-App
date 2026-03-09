import os
import pandas as pd
import requests
import time
import numpy as np

# CONFIG
FILENAME = "Sample_Data_5_Devices.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "http://localhost:8000/api/analyze-behaviour"
NUM_DEVICES = 5
NUM_FEATURES = 8

def main():
    print(f"Loading {FILENAME}...")
    try:
        # Remove any text
        simulated_devices_df = pd.read_csv(FILENAME, header=None)
        simulated_devices_df = simulated_devices_df.apply(pd.to_numeric, errors='coerce')
        simulated_devices_df = simulated_devices_df.dropna()
        
    except Exception:
        print("Error loading the csv of simulated device data")
        return

    # Process each device
    for current_device_index in range(NUM_DEVICES):
        device_id = f"Device-{current_device_index+1}"
        
        try:
            # Device 0 gets rows 0-7, Device 1 gets rows 8-15, etc.
            start_row = current_device_index * NUM_FEATURES
            end_row = start_row + NUM_FEATURES
            
            device_features_df = simulated_devices_df.iloc[start_row:end_row, :] 
            device_history = device_features_df.T.values
            
            # only send the last 300 interactions
            if device_history.shape[0] > 300:
                 device_history = device_history[-300:, :]

            history = device_history.tolist()
            payload = {
                "device_id": device_id,
                "history": history
            }
            print(f"Sending {device_id}...{history}")
            # Send to backend for CNN analysis
            print(f"Sending {device_id}...", end=" ")
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"Class: {result['device_class_pred']} | Status: {result['status']}")
            else:
                print(f"Failed: {response.text}")
                
        except Exception as e:
            print(f"Error processing {device_id}: {e}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()