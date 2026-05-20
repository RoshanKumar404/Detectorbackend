import tflite_runtime.interpreter as tflite
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import numpy as np
import io
import os

# Configuration - must match training config
IMG_SIZE = (224, 224)
CLASS_NAMES = ['photos', 'waterlogged']  # Alphabetical order

class AIService:
    """
    Singleton service that loads the trained TFLite model once
    and provides a predict() method for image classification.
    """
    _instance = None
    _interpreter = None
    _input_details = None
    _output_details = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._interpreter is not None:
            return

        # Model is in the root directory of DetectorBackSupport
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'model.tflite')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"TFLite model not found at {model_path}. Please convert your keras model first.")
        
        print(f"[AI Service] Loading lightweight TFLite model from {model_path}...")
        
        # Load the TFLite runtime engine
        self._interpreter = tflite.Interpreter(model_path=model_path)
        self._interpreter.allocate_tensors()
        
        # Get structural details for inputs and outputs
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()
        
        print("[AI Service] TFLite Model loaded successfully!")

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
        
        # 5. Run prediction via TFLite Interpreter
        self._interpreter.set_tensor(self._input_details[0]['index'], img_array)
        self._interpreter.invoke()
        
        # 6. Extract results
        predictions = self._interpreter.get_tensor(self._output_details[0]['index'])
        scores = predictions[0]
        
        # 7. Map scores to class names
        raw_scores = {CLASS_NAMES[i]: float(scores[i]) for i in range(len(CLASS_NAMES))}
        
        # 8. Get the predicted class
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
