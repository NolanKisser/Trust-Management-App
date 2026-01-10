import numpy as np
import tensorflow as tf
import joblib
import os

class TrustModelPipeline:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = "CNNv2_Filters64-128-256-Kernels20-15-5-Swish_E500-Best.keras"
        self.scaler_path = "scaler.pkl"

    def load_resources(self) -> bool:
        """
        Load CNN model and Scaler
        """
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path, compile=False) #compile set to False to fix version mismatch
            except Exception as e:
                print(f"ERROR loading CNN: {e}")
                return False
        else:
            print("ERROR: CNN model not found.")
            return False

        if os.path.exists(self.scaler_path):
            try:
                self.scaler = joblib.load(self.scaler_path)
            except Exception as e:
                print(f"ERROR loading scaler: {e}")
                return False
        else:
            print("ERROR: Scaler not found.")
            return False

        return True

    def predict_trust(self, interactions: list) -> int:
        """
        Passes device interaction data into CNN to get a behavioural prediction
        Params:
        - interactions: list where each row in an interaction, and each column is a feature (Trust, SIA, NTA, NDA, SSE, SSA)
        """
        if not self.model or not self.scaler:
            print("Resources not loaded. Returning mock.")
            return -1.0

        try:
            X_raw = np.array(interactions) #(Interactions * Features)

            if X_raw.shape != (300, 6): #TODO modify if model changes
                print(f"Shape incorrect: Expected (300, 6), got {X_raw.shape}. Returning Mock.")
                return -1.0

            X_flattened_input = X_raw.T.reshape(1, -1) # (1, Interactions * Features)
            X_scaled_flat = self.scaler.transform(X_flattened_input)
            X_reshaped = X_scaled_flat.reshape(1, 6, 300) #(Batch, Features, Interactions)
            X_input = X_reshaped.transpose(0, 2, 1) # (Batch, Interactions, Features)
            
            # Get device behaviour prediction as int instead of one-hot
            prediction_distribution = self.model.predict(X_input, verbose=0)[0]
            prediction_index = np.argmax(prediction_distribution)
            device_class_int = int(prediction_index + 1)
            
            return device_class_int

        except Exception as e:
            print(f"Prediction Logic Error: {e}. Returning Mock.")
            return -1.0