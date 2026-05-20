import tensorflow as tf

# Run this locally to generate your 'model.tflite' file
print("Loading model...")
model = tf.keras.models.load_model('saved_model.keras')

print("Converting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

print("Saving model.tflite...")
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)

print("Done!")
