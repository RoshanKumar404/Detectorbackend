import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import io
import os

# Configuration - must match training config
IMG_SIZE = (224, 224)
CLASS_NAMES = ['photos', 'waterlogged']  # Alphabetical order (as Keras assigns)

class AIService:
    """
    Singleton service that loads the trained Keras model once
    and provides a predict() method for image classification.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return

        # Model is in the root directory of DetectorBackSupport
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'saved_model.keras')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please train the model first.")
        
        print(f"[AI Service] Loading model from {model_path}...")
        self._model = load_model(model_path)
        print("[AI Service] Model loaded successfully!")

    def predict(self, image_bytes: bytes) -> dict:
        self._load_model()

        # 1. Decode image
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # 2. Resize to model input size
        image = image.resize(IMG_SIZE)
        
        # 3. Convert to numpy array and normalize
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 4. Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        # 5. Run prediction
        predictions = self._model.predict(img_array, verbose=0)
        scores = predictions[0]
        
        # 6. Map scores to class names
        raw_scores = {CLASS_NAMES[i]: float(scores[i]) for i in range(len(CLASS_NAMES))}
        
        # 7. Get the predicted class
        predicted_index = int(np.argmax(scores))
        predicted_class = CLASS_NAMES[predicted_index]
        confidence = float(scores[predicted_index])
        
        return {
            'prediction': predicted_class,
            'confidence': round(confidence, 4),
            'raw_scores': raw_scores,
        }

# Global singleton instance
ai_service = AIService()
