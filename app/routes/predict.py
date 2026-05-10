from flask import Blueprint, request, jsonify

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/', methods=['POST'])
def predict_image():
    """
    Accepts an image file via multipart/form-data and returns
    the AI model's waterlogging prediction.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    
    if image_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        image_bytes = image_file.read()
        
        # Lazy import to avoid loading TF at app startup unless needed
        from app.services.ai_service import ai_service
        result = ai_service.predict(image_bytes)
        
        return jsonify(result), 200

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"[Predict Error] {e}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
