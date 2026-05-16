"""
train.py
========
Script training model Multi-Modal klasifikasi penyakit ruam kulit.
Menggabungkan data citra (CNN) dan gejala klinis (MLP).

Cara menjalankan (dari root folder):
    (venv) D:\program pi> python src\train.py

Output:
    - model terbaik    : model\best_model.h5
    - grafik training  : model\training_history.png
    - laporan evaluasi : model\evaluation_report.txt
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.callbacks import (
    ModelCheckpoint, EarlyStopping,
    ReduceLROnPlateau, TensorBoard
)

# ── Path otomatis ──
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from preprocessing  import load_data
from model_fusion   import build_fusion_model, compile_model, unfreeze_for_finetuning


# ─────────────────────────────────────────────
# KONFIGURASI TRAINING
# ─────────────────────────────────────────────

BATCH_SIZE      = 16
EPOCHS_PHASE1   = 30    # training awal (backbone frozen)
EPOCHS_PHASE2   = 20    # fine-tuning (backbone sebagian dibuka)
MODEL_DIR       = os.path.join(ROOT_DIR, 'model')
CLASSES         = ['campak', 'rubella', 'cacar']

os.makedirs(MODEL_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# HELPER: BUAT DATASET TENSORFLOW
# ─────────────────────────────────────────────

def make_dataset(X_img, X_sym, y, batch_size, shuffle=True):
    """
    Buat tf.data.Dataset dari array numpy.
    Lebih efisien dari fit() langsung dengan numpy array besar.
    """
    ds = tf.data.Dataset.from_tensor_slices(
        ({'input_citra': X_img, 'input_gejala': X_sym}, y)
    )
    if shuffle:
        ds = ds.shuffle(buffer_size=len(y), seed=42)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


# ─────────────────────────────────────────────
# HELPER: PLOT HISTORY
# ─────────────────────────────────────────────

def plot_history(history, phase_name='phase1'):
    """Simpan grafik accuracy dan loss ke folder model/."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    axes[0].plot(history.history['accuracy'],     label='Train Accuracy')
    axes[0].plot(history.history['val_accuracy'], label='Val Accuracy')
    axes[0].set_title(f'Accuracy — {phase_name}')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Accuracy')
    axes[0].legend()
    axes[0].grid(True)

    # Loss
    axes[1].plot(history.history['loss'],     label='Train Loss')
    axes[1].plot(history.history['val_loss'], label='Val Loss')
    axes[1].set_title(f'Loss — {phase_name}')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Loss')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    save_path = os.path.join(MODEL_DIR, f'history_{phase_name}.png')
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  Grafik disimpan: {save_path}")


# ─────────────────────────────────────────────
# HELPER: EVALUASI & LAPORAN
# ─────────────────────────────────────────────

def evaluate_model(model, ds_test, X_img_test, X_sym_test, y_test):
    """
    Evaluasi model pada data test.
    Simpan classification report dan confusion matrix.
    """
    print("\n=== EVALUASI MODEL ===")

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


# ─────────────────────────────────────────────
# MAIN TRAINING
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  TRAINING MULTIMODAL SKIN RASH CLASSIFIER")
    print("=" * 60)

    # ── 1. Load Data ──
    print("\n[1/5] Memuat dataset...")
    data     = load_data(os.path.join(ROOT_DIR, 'data'))
    img_data = data['images']
    sym_data = data['symptoms']

    X_img_train = img_data['X_train']
    X_img_val   = img_data['X_val']
    X_img_test  = img_data['X_test']

    X_sym_train = sym_data['X_train']
    X_sym_val   = sym_data['X_val']
    X_sym_test  = sym_data['X_test']

    y_train = img_data['y_train']
    y_val   = img_data['y_val']
    y_test  = img_data['y_test']

    print(f"\n  Ringkasan data:")
    print(f"  Train : {len(y_train)} sampel")
    print(f"  Val   : {len(y_val)} sampel")
    print(f"  Test  : {len(y_test)} sampel")

    # ── 2. Buat Dataset ──
    print("\n[2/5] Membuat tf.data.Dataset...")
    ds_train = make_dataset(X_img_train, X_sym_train, y_train, BATCH_SIZE, shuffle=True)
    ds_val   = make_dataset(X_img_val,   X_sym_val,   y_val,   BATCH_SIZE, shuffle=False)
    ds_test  = make_dataset(X_img_test,  X_sym_test,  y_test,  BATCH_SIZE, shuffle=False)

    # ── 3. Bangun Model ──
    print("\n[3/5] Membangun model...")
    model = build_fusion_model()
    model = compile_model(model)
    print(f"  Total parameter: {model.count_params():,}")

    # ── 4. PHASE 1: Training Awal (backbone frozen) ──
    print(f"\n[4/5] PHASE 1 — Training awal ({EPOCHS_PHASE1} epoch, backbone frozen)")

    callbacks_p1 = [
        ModelCheckpoint(
            filepath        = os.path.join(MODEL_DIR, 'best_model.keras'),
            monitor         = 'val_accuracy',
            save_best_only  = True,
            verbose         = 1
        ),
        EarlyStopping(
            monitor         = 'val_accuracy',
            patience        = 8,
            restore_best_weights = True,
            verbose         = 1
        ),
        ReduceLROnPlateau(
            monitor         = 'val_loss',
            factor          = 0.5,
            patience        = 4,
            min_lr          = 1e-7,
            verbose         = 1
        ),
    ]

    history_p1 = model.fit(
        ds_train,
        validation_data = ds_val,
        epochs          = EPOCHS_PHASE1,
        callbacks       = callbacks_p1,
        verbose         = 1
    )

    plot_history(history_p1, phase_name='phase1_frozen')

    # ── 5. PHASE 2: Fine-tuning ──
    print(f"\n[5/5] PHASE 2 — Fine-tuning ({EPOCHS_PHASE2} epoch, backbone sebagian dibuka)")

    model = unfreeze_for_finetuning(model, num_layers_to_unfreeze=30)

    callbacks_p2 = [
        ModelCheckpoint(
            filepath        = os.path.join(MODEL_DIR, 'best_model.keras'),
            monitor         = 'val_accuracy',
            save_best_only  = True,
            verbose         = 1
        ),
        EarlyStopping(
            monitor         = 'val_accuracy',
            patience        = 6,
            restore_best_weights = True,
            verbose         = 1
        ),
        ReduceLROnPlateau(
            monitor         = 'val_loss',
            factor          = 0.5,
            patience        = 3,
            min_lr          = 1e-8,
            verbose         = 1
        ),
    ]

    history_p2 = model.fit(
        ds_train,
        validation_data = ds_val,
        epochs          = EPOCHS_PHASE2,
        callbacks       = callbacks_p2,
        verbose         = 1
    )

    plot_history(history_p2, phase_name='phase2_finetune')

    # ── 6. Evaluasi ──
    evaluate_model(model, ds_test, X_img_test, X_sym_test, y_test)

    # ── 7. Simpan Model Final ──
    final_path = os.path.join(MODEL_DIR, 'final_model.keras')
    model.save(final_path)
    print(f"\nModel final disimpan: {final_path}")

    print("\n" + "=" * 60)
    print("  TRAINING SELESAI!")
    print(f"  Cek folder: {MODEL_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()