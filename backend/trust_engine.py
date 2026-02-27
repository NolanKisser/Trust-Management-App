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
        Load CNN and scaler so we can run device behaviour classification predictions
        """
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path, compile=False) #compile set to False to fix version mismatch
            except Exception as e:
                print(f"ERROR: Can't load CNN for device behaviour classification: {e}")
                return False
        else:
            print("ERROR: CNN not found.")
            return False

        if os.path.exists(self.scaler_path):
            try:
                self.scaler = joblib.load(self.scaler_path)
            except Exception as e:
                print(f"ERROR: Can't load scaler: {e}")
                return False
        else:
            print("ERROR: Scaler not found.")
            return False

        return True

    def predict_trust(self, interactions: list) -> int:
        """
        Passes device interaction data into CNN to get a behavioural prediction
        - interactions: list where each row in an interaction, and each column is an attribute (Trust, SIA, NTA, NDA, SSE, SSA/SSMA)
        """
        if not self.model or not self.scaler:
            print("ERROR: Resources not loaded. Returning mock.")
            return -1.0

        try:
            X_raw = np.array(interactions) #(interactions * attributes)

            if X_raw.shape != (300, 8): 
                print(f"Shape incorrect: Expected (300, 8), got {X_raw.shape}. Returning Mock.")
                return -1.0

            # Scale and then reformat
            X_scaled = self.scaler.transform(X_raw) # (300 rows/interactions, 6 columns/attributes)
            X_input = X_scaled.reshape(1, 300, 8) #(batch, interactions, attributes)
            
            # Get device behaviour prediction as int instead of one-hot
            prediction_distribution = self.model.predict(X_input, verbose=0)[0]
            prediction_index = np.argmax(prediction_distribution)
            device_class_int = int(prediction_index + 1)
            
            return device_class_int

        except Exception as e:
            print(f"ERROR for prediction logic: {e}. Returning Mock.")
            return -1.0