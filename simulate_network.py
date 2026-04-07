import os
import pandas as pd
import requests
import time

# CONFIG
FILENAME = "Sample_Data_5_Devices.csv"
LARGE_FILE = "Sample Data 21 Devices - 8 Attr.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "http://localhost:8000/api/analyze-behaviour"
NUM_DEVICES = 5
NUM_FEATURES = 8
# Dashboard ids -> 1-based block index in "Sample Data 21 Devices - 8 Attr.csv"
DEVICE_3_BLOCK_INDEX = 21
DEVICE_5_BLOCK_INDEX = 11

def main():
    path_small = os.path.join(BASE_DIR, FILENAME)
    path_large = os.path.join(BASE_DIR, LARGE_FILE)

    print(f"Loading {FILENAME}...")
    try:
        simulated_devices_df = pd.read_csv(path_small, header=None)
        simulated_devices_df = simulated_devices_df.apply(pd.to_numeric, errors='coerce')
        simulated_devices_df = simulated_devices_df.dropna()
        large_df = pd.read_csv(path_large, header=None)
    except Exception:
        print("Error loading the csv of simulated device data")
        return

    # Process each device
    for current_device_index in range(NUM_DEVICES):
        device_id = f"Device-{current_device_index+1}"

        try:
            if current_device_index == 2:
                # Device-3: profile 21 in 21-device file (rows 160-167)
                start_row = (DEVICE_3_BLOCK_INDEX * 8) - 8
                end_row = start_row + NUM_FEATURES
                block = large_df.iloc[start_row:end_row, :]
                device_features_df = block.apply(pd.to_numeric, errors='coerce').dropna()
            elif current_device_index == 4:
                # Device-5: profile 11 (rows 80-87)
                start_row = (DEVICE_5_BLOCK_INDEX * 8) - 8
                end_row = start_row + NUM_FEATURES
                block = large_df.iloc[start_row:end_row, :]
                device_features_df = block.apply(pd.to_numeric, errors='coerce').dropna()
            elif current_device_index == 3:
                # Device-4: 4th 8-row block in small CSV (rows 24-31); skip old device-3 rows 16-23
                start_row = 3 * NUM_FEATURES
                end_row = start_row + NUM_FEATURES
                device_features_df = simulated_devices_df.iloc[start_row:end_row, :]
            else:
                # Device-1, Device-2: rows 0-7 and 8-15
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
            # Send to backend for CNN analysis
            if current_device_index == 2:
                prof = DEVICE_3_BLOCK_INDEX
            elif current_device_index == 4:
                prof = DEVICE_5_BLOCK_INDEX
            elif current_device_index == 3:
                prof = "small CSV block 4"
            else:
                prof = current_device_index + 1
            print(f"Sending {device_id} (profile {prof})...", end=" ")
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
