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

    def load_resources(self):
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load Model with compile=False to fix version mismatch
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

        # Load Scaler
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
            # Convert to Numpy Array (Shape: 300, 6)
            raw_data = np.array(interactions)
            
            # Validation
            if raw_data.shape != (300, 6):
                print(f"Shape Mismatch: Expected (300, 6), got {raw_data.shape}")
                return 0.5

            flattened_input = raw_data.T.reshape(1, -1) # Shape becomes (1, 1800)

            scaled_flat = self.scaler.transform(flattened_input)

            # Reshape for CNN (Batch, Features, Interactions) -> (1, 6, 300)
            reshaped_temp = scaled_flat.reshape(1, 6, 300)
            
            # Transpose(Batch, Interactions, Features) -> (1, 300, 6) - consistent with training format
            input_tensor = reshaped_temp.transpose(0, 2, 1)

            prediction_distribution = self.model.predict(input_tensor, verbose=0)[0]
            
            predicted_class_index = np.argmax(prediction_distribution)
            #TODO useful metric
            trust_score = predicted_class_index / 20.0
            
            return float(trust_score)

        except Exception as e:
            print(f"Prediction Logic Error: {e}")
            return 0.5