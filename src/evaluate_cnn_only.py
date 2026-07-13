import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import tensorflow as tf

SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from preprocessing import load_data
from evaluate_only import align_symptom_data, make_dataset

BATCH_SIZE = 16
MODEL_DIR = os.path.join(ROOT_DIR, 'model')
CLASSES = ['campak', 'rubella', 'cacar']

def main():
    print("=" * 60)
    print("  EVALUASI CNN ONLY (TANPA GEJALA)")
    print("=" * 60)

    model_path = os.path.join(MODEL_DIR, 'best_model.keras')
    data = load_data(os.path.join(ROOT_DIR, 'data'))
    img_data = data['images']
    
    X_img_test = img_data['X_test']
    y_test = img_data['y_test']
    
    # KUNCI CNN ONLY: Set semua gejala ke NOL agar MLP tidak memberikan pengaruh
    X_sym_test = np.zeros((len(X_img_test), 10), dtype=np.float32)

    model = tf.keras.models.load_model(model_path)

    y_pred_prob = model.predict({'input_citra': X_img_test, 'input_gejala': X_sym_test}, verbose=0)
    y_pred = np.argmax(y_pred_prob, axis=1)

    report = classification_report(y_test, y_pred, target_names=CLASSES)
    print("\nClassification Report (CNN ONLY):")
    print(report)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Oranges', xticklabels=CLASSES, yticklabels=CLASSES)
    plt.title('Confusion Matrix - CNN Only (Tanpa Gejala)')
    plt.xlabel('Prediksi')
    plt.ylabel('Aktual')
    plt.tight_layout()
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix_cnn.png')
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"Confusion matrix CNN disimpan: {cm_path}")

    # Simpan report text
    with open(os.path.join(MODEL_DIR, 'evaluation_report_cnn.txt'), 'w') as f:
        f.write("Classification Report (CNN ONLY):\n")
        f.write(report)

if __name__ == '__main__':
    main()
