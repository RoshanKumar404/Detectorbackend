import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import numpy as np
import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve, f1_score
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Configs
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.getenv('DATASET_DIR', os.path.join(ROOT_DIR, 'dataset'))
METRICS_DIR = os.path.join(ROOT_DIR, 'ml_pipeline', 'metrics')
MODEL_PATH = os.path.join(ROOT_DIR, 'saved_model.keras')
METADATA_PATH = os.path.join(ROOT_DIR, 'model_metadata.json')
IMG_SIZE = (224, 224)
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 16)) # Lower batch size for stability
EPOCHS = int(os.getenv('EPOCHS', 15))         # Enough epochs to show curve progression
NUM_CLASSES = 2
CLASS_NAMES = ['Not-WaterLogged', 'waterlogged']

def build_model(num_classes):
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')
    base_model.trainable = False
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=[
            'accuracy',
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    return model

def main():
    train_dir = os.path.join(DATASET_DIR, 'train')
    val_dir = os.path.join(DATASET_DIR, 'val')
    os.makedirs(METRICS_DIR, exist_ok=True)

    print("Loading data...")
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASS_NAMES,
        shuffle=True
    )

    # For evaluation we want sequential (no shuffle) to align predictions with ground truths
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASS_NAMES,
        shuffle=False
    )

    if train_generator.class_indices != val_generator.class_indices:
        raise ValueError(
            f"Train/validation class mismatch: {train_generator.class_indices} vs {val_generator.class_indices}"
        )

    print("Building and training transfer learning model...")
    model = build_model(NUM_CLASSES)
    
    # Train
    history = model.fit(
        train_generator,
        epochs=EPOCHS,
        validation_data=val_generator,
        verbose=2
    )

    # Save model
    model.save(MODEL_PATH)
    print(f"Model saved successfully as {MODEL_PATH}")

    metadata = {
        "class_names": CLASS_NAMES,
        "class_indices": train_generator.class_indices,
        "image_size": IMG_SIZE,
        "model_file": "model.tflite",
        "keras_model_file": "saved_model.keras"
    }
    with open(METADATA_PATH, 'w', encoding='utf-8') as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
    print(f"Model metadata saved successfully as {METADATA_PATH}")

    # Get predictions
    print("Running evaluation predictions...")
    y_pred = model.predict(val_generator, verbose=1)
    y_true = val_generator.classes # ground truths
    y_pred_probs = y_pred[:, 1]    # probability of 'waterlogged'
    y_pred_labels = np.argmax(y_pred, axis=1)

    epochs_range = range(1, EPOCHS + 1)

    # 1. & 2. Training and Validation Loss Curves
    plt.figure(figsize=(8, 5))
    plt.plot(epochs_range, history.history['loss'], label='Training Loss', color='#c0392b', marker='o')
    plt.plot(epochs_range, history.history['val_loss'], label='Validation Loss', color='#2980b9', marker='s')
    plt.title('Training & Validation Loss Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'loss_curves.png'), dpi=150)
    plt.close()
    print("1 & 2. Saved Loss Curves.")

    # 3. Accuracy Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs_range, history.history['accuracy'], label='Training Accuracy', color='#27ae60', marker='o')
    plt.plot(epochs_range, history.history['val_accuracy'], label='Validation Accuracy', color='#d35400', marker='s')
    plt.title('Accuracy Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'accuracy_curve.png'), dpi=150)
    plt.close()
    print("3. Saved Accuracy Curve.")

    # 4. Precision Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs_range, history.history['precision'], label='Training Precision', color='#8e44ad', marker='o')
    plt.plot(epochs_range, history.history['val_precision'], label='Validation Precision', color='#16a085', marker='s')
    plt.title('Precision Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Precision')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'precision_curve.png'), dpi=150)
    plt.close()
    print("4. Saved Precision Curve.")

    # 5. Recall Curve
    plt.figure(figsize=(8, 5))
    plt.plot(epochs_range, history.history['recall'], label='Training Recall', color='#2c3e50', marker='o')
    plt.plot(epochs_range, history.history['val_recall'], label='Validation Recall', color='#f39c12', marker='s')
    plt.title('Recall Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Recall')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'recall_curve.png'), dpi=150)
    plt.close()
    print("5. Saved Recall Curve.")

    # 6. F1 Score over Thresholds
    thresholds = np.linspace(0.01, 0.99, 100)
    f1_scores = [f1_score(y_true, (y_pred_probs >= t).astype(int)) for t in thresholds]
    plt.figure(figsize=(8, 5))
    plt.plot(thresholds, f1_scores, label='F1 Score', color='#e67e22', linewidth=2)
    plt.title('F1 Score vs Classification Threshold')
    plt.xlabel('Threshold')
    plt.ylabel('F1 Score')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    best_f1_index = int(np.argmax(f1_scores))
    best_threshold = float(thresholds[best_f1_index])
    best_f1 = float(f1_scores[best_f1_index])
    plt.savefig(os.path.join(METRICS_DIR, 'f1_score_curve.png'), dpi=150)
    plt.close()
    print("6. Saved F1 Score Curve.")

    # 7. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred_labels)
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
           title='Confusion Matrix',
           ylabel='True Label',
           xlabel='Predicted Label')
    # Loop over data dimensions and create text annotations.
    fmt = 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=14, fontweight='bold')
    fig.tight_layout()
    plt.savefig(os.path.join(METRICS_DIR, 'confusion_matrix.png'), dpi=150)
    plt.close()
    print("7. Saved Confusion Matrix.")

    # 8. Precision-Recall Curve
    precision_vals, recall_vals, _ = precision_recall_curve(y_true, y_pred_probs)
    plt.figure(figsize=(8, 5))
    plt.plot(recall_vals, precision_vals, color='#1abc9c', linewidth=2, label='PR Curve')
    plt.title('Precision-Recall Curve')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.savefig(os.path.join(METRICS_DIR, 'precision_recall_curve.png'), dpi=150)
    plt.close()
    print("8. Saved Precision-Recall Curve.")

    # 9. Confidence Curve (Prediction Certainty Distribution)
    plt.figure(figsize=(8, 5))
    plt.hist(y_pred_probs[y_true == 1], bins=15, alpha=0.6, label='Waterlogged Class', color='#e74c3c')
    plt.hist(y_pred_probs[y_true == 0], bins=15, alpha=0.6, label='Dry/Photos Class', color='#2ecc71')
    plt.title('Confidence Distribution (Prediction Certainty)')
    plt.xlabel('Probability of Waterlogged')
    plt.ylabel('Count of Images')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'confidence_curve.png'), dpi=150)
    plt.close()
    print("9. Saved Confidence Curve.")

    # 10. ROC Curve
    fpr, tpr, _ = roc_curve(y_true, y_pred_probs)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 5))
    plt.plot(fpr, tpr, color='#2980b9', linewidth=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend(loc="lower right")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(METRICS_DIR, 'roc_curve.png'), dpi=150)
    plt.close()
    print("10. Saved ROC Curve.")

    summary = {
        "dataset_dir": DATASET_DIR,
        "class_names": CLASS_NAMES,
        "class_indices": train_generator.class_indices,
        "train_samples": int(train_generator.samples),
        "validation_samples": int(val_generator.samples),
        "epochs": EPOCHS,
        "final_train_accuracy": float(history.history['accuracy'][-1]),
        "final_validation_accuracy": float(history.history['val_accuracy'][-1]),
        "final_train_loss": float(history.history['loss'][-1]),
        "final_validation_loss": float(history.history['val_loss'][-1]),
        "final_train_precision": float(history.history['precision'][-1]),
        "final_validation_precision": float(history.history['val_precision'][-1]),
        "final_train_recall": float(history.history['recall'][-1]),
        "final_validation_recall": float(history.history['val_recall'][-1]),
        "best_f1_threshold": best_threshold,
        "best_f1_score": best_f1,
        "roc_auc": float(roc_auc),
        "confusion_matrix": cm.tolist()
    }
    with open(os.path.join(METRICS_DIR, 'metrics_summary.json'), 'w', encoding='utf-8') as summary_file:
        json.dump(summary, summary_file, indent=2)
    print("Saved metrics_summary.json.")

    print("\nAll 10 requested performance charts have been saved successfully inside ml_pipeline/metrics/!")

if __name__ == '__main__':
    main()
