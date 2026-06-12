"""
evaluate_only.py
================
Evaluasi model yang sudah dilatih tanpa melatih ulang.
Cocok untuk cepat melihat hasil model terbaik.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import tensorflow as tf

# ── Path otomatis ──
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from preprocessing import load_data


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────

BATCH_SIZE      = 16
MODEL_DIR       = os.path.join(ROOT_DIR, 'model')
CLASSES         = ['campak', 'rubella', 'cacar']

os.makedirs(MODEL_DIR, exist_ok=True)


def align_symptom_data(X_sym, target_size):
    """Sejajarkan jumlah sampel gejala dengan jumlah sampel citra."""
    if len(X_sym) == target_size:
        return X_sym
    elif len(X_sym) < target_size:
        n_repeats = target_size // len(X_sym) + 1
        X_sym_repeated = np.tile(X_sym, (n_repeats, 1))
        X_sym_aligned = X_sym_repeated[:target_size]
        return X_sym_aligned
    else:
        return X_sym[:target_size]


def make_dataset(X_img, X_sym, y, batch_size, shuffle=True):
    """Buat tf.data.Dataset dari array numpy."""
    X_sym = align_symptom_data(X_sym, len(X_img))
    
    ds = tf.data.Dataset.from_tensor_slices(
        ({'input_citra': X_img, 'input_gejala': X_sym}, y)
    )
    if shuffle:
        ds = ds.shuffle(buffer_size=len(y), seed=42)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def evaluate_model(model, ds_test, X_img_test, X_sym_test, y_test):
    """Evaluasi model pada data test."""
    print("\n=== EVALUASI MODEL ===")

    # Sejajarkan gejala dengan citra sebelum prediksi
    X_sym_test = align_symptom_data(X_sym_test, len(X_img_test))
    
    # Prediksi
    y_pred_prob = model.predict(
        {'input_citra': X_img_test, 'input_gejala': X_sym_test},
        verbose=0
    )
    y_pred = np.argmax(y_pred_prob, axis=1)

    # Akurasi test
    test_loss, test_acc = model.evaluate(ds_test, verbose=0)
    print(f"  Test Loss    : {test_loss:.4f}")
    print(f"  Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")

    # Classification Report
    report = classification_report(y_test, y_pred, target_names=CLASSES)
    print("\n  Classification Report:")
    print(report)

    # Simpan laporan ke file
    report_path = os.path.join(MODEL_DIR, 'evaluation_report.txt')
    with open(report_path, 'w') as f:
        f.write(f"Test Loss    : {test_loss:.4f}\n")
        f.write(f"Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)\n\n")
        f.write("Classification Report:\n")
        f.write(report)
    print(f"  Laporan disimpan: {report_path}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=CLASSES, yticklabels=CLASSES)
    plt.title('Confusion Matrix')
    plt.xlabel('Prediksi')
    plt.ylabel('Aktual')
    plt.tight_layout()
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"  Confusion matrix disimpan: {cm_path}")

    return test_acc


def main():
    print("=" * 60)
    print("  EVALUASI MODEL (TANPA TRAINING ULANG)")
    print("=" * 60)

    # Cek apakah model sudah ada
    model_path = os.path.join(MODEL_DIR, 'best_model.keras')
    if not os.path.exists(model_path):
        print(f"\n❌ Model tidak ditemukan: {model_path}")
        print("Jalankan train.py terlebih dahulu untuk melatih model")
        return

    # ── 1. Load Data ──
    print("\n[1/3] Memuat dataset...")
    data     = load_data(os.path.join(ROOT_DIR, 'data'))
    img_data = data['images']
    sym_data = data['symptoms']

    X_img_test  = img_data['X_test']
    X_sym_test  = sym_data['X_test']
    y_test      = img_data['y_test']

    print(f"\n  Test sampel: {len(y_test)}")

    # ── 2. Load Model ──
    print("\n[2/3] Memuat model terbaik...")
    model = tf.keras.models.load_model(model_path)
    print(f"  Model dimuat dari: {model_path}")
    print(f"  Total parameter: {model.count_params():,}")

    # ── 3. Buat Test Dataset ──
    print("\n[3/3] Membuat tf.data.Dataset...")
    ds_test = make_dataset(X_img_test, X_sym_test, y_test, BATCH_SIZE, shuffle=False)

    # ── 4. Evaluasi ──
    evaluate_model(model, ds_test, X_img_test, X_sym_test, y_test)

    print("\n" + "=" * 60)
    print("  EVALUASI SELESAI!")
    print(f"  Hasil disimpan di: {MODEL_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
