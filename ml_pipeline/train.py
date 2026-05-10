import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import os

# Configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
NUM_CLASSES = 2  # E.g., photos, waterlogged
EPOCHS = 5

def build_transfer_learning_model(num_classes):
    """
    Builds a MobileNetV2 model with a custom classification head.
    Base layers are initially frozen.
    """
    # Load MobileNetV2 without the top classification layer
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), 
                             include_top=False, 
                             weights='imagenet')
    
    # Freeze the base model to only train the new classification head
    base_model.trainable = False 

    # Add custom head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x) # Dropout for regularization
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    return model, base_model

def train_model(train_dir, val_dir, output_model_dir='saved_model.keras'):
    """
    Trains the custom classification head.
    """
    print("Setting up data generators...")
    
    # Data augmentation for training
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )
    
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )
    
    # Build model
    model, base_model = build_transfer_learning_model(train_generator.num_classes)
    model.summary()
    
    print("\n--- Starting Phase 1: Training custom head ---")
    history = model.fit(
        train_generator,
        epochs=EPOCHS,
        validation_data=val_generator
    )
    
    # Save the model
    output_dir = os.path.dirname(output_model_dir)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    model.save(output_model_dir)
    print(f"Model saved to {output_model_dir}")
    
    return model

if __name__ == '__main__':
    print("Starting Model Training...")
    train_model('./dataset/train', './dataset/val')
