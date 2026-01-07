import numpy as np
import tensorflow as tf
import joblib
import os

class TrustModelPipeline:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = "CNNv2_Filters64-128-256-Kernels20-15-5-Swish_E500-Best.h5"
        self.scaler_path = "scaler.pkl"

    def load_resources(self):
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Load Model with compile=False to fix version mismatch
        model_full_path = os.path.join(current_dir, self.model_path)
        if os.path.exists(model_full_path):
            try:
                # compile=False is the magic fix here
                self.model = tf.keras.models.load_model(model_full_path, compile=False)
                print(f"Model loaded: {self.model_path} (Inference Mode)")
            except Exception as e:
                print(f"Model Load Error: {e}")
        else:
            print(f"FILE MISSING: Expected model at {model_full_path}")

        # 2. Load Scaler
        scaler_full_path = os.path.join(current_dir, self.scaler_path)
        if os.path.exists(scaler_full_path):
            try:
                self.scaler = joblib.load(scaler_full_path)
                print(f"Scaler loaded: {self.scaler_path}")
            except Exception as e:
                print(f"Scaler Load Error: {e}")
        else:
            print(f"FILE MISSING: Expected scaler at {scaler_full_path}")

    def predict_trust(self, interactions: list) -> float:
        """
        Expects a list of 300 lists, where each inner list has 6 features:
        [Trust, SIA, NTA, NDA, SSE, SSA]
        """
        if not self.model or not self.scaler:
            print("Resources not loaded. Returning mock.")
            return 0.5

        try:
            # 1. Convert to Numpy Array (Shape: 300, 6)
            raw_data = np.array(interactions)
            
            # Validation: Ensure we have exactly 300 interactions of 6 features
            if raw_data.shape != (300, 6):
                print(f"Shape Mismatch: Expected (300, 6), got {raw_data.shape}")
                return 0.5

            # 2. Scale the Data (Standardization)
            scaled_data = self.scaler.transform(raw_data)

            # 3. Reshape for CNN (Batch, Interactions, Features) -> (1, 300, 6)
            input_tensor = np.expand_dims(scaled_data, axis=0)

            # 4. Inference
            prediction_distribution = self.model.predict(input_tensor, verbose=0)[0]
            
            # 5. Decode Output
            # Your model outputs 21 classes (0.00, 0.05, ... 1.00).
            # We take the argmax (highest probability class) and map it to a score.
            predicted_class_index = np.argmax(prediction_distribution)
            
            # Map index 0-20 to trust score 0.0 - 1.0
            trust_score = predicted_class_index / 20.0
            
            return float(trust_score)

        except Exception as e:
            print(f"Prediction Logic Error: {e}")
            return 0.5