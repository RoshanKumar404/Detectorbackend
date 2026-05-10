import tensorflow as tf
import os

def convert_saved_model_to_tflite(saved_model_dir, output_path='waterlogging_model.tflite'):
    """
    Converts a TensorFlow SavedModel or Keras .h5 model to TFLite format
    optimized for mobile devices.
    """
    print(f"Loading model from {saved_model_dir}...")
    
    # If the model was saved as a SavedModel directory
    if os.path.isdir(saved_model_dir):
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    # If the model was saved as a Keras file (.h5 or .keras)
    else:
        model = tf.keras.models.load_model(saved_model_dir)
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
    # Optional: Enable optimization (quantization) to reduce model size for mobile
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    print("Converting model to TensorFlow Lite format...")
    tflite_model = converter.convert()
    
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
        
    print(f"Conversion complete! Model saved to {output_path}")
    print(f"Size: {len(tflite_model) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    print("Starting conversion to TFLite...")
    convert_saved_model_to_tflite('saved_model.keras', 'waterlogging_model.tflite')
