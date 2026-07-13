"""
train.py
========
Script training model Multi-Modal FusionNet (MobileNetV2 CNN + MLP)
untuk klasifikasi penyakit ruam kulit: Campak, Rubella, Cacar Air.

Skema split      : 80% train, 20% test (gambar sudah ada di folder terpisah)
Validasi internal: 10% diambil dari data train saat runtime
Augmentasi online: Flip, rotasi, brightness via tf.data pipeline (data train saja)

Alur Training 2-Phase:
  - Phase 1 (30 epoch): Backbone MobileNetV2 di-freeze, hanya head yang dilatih
  - Phase 2 (20 epoch): Fine-tuning 30 layer terakhir backbone dengan LR sangat kecil

Output yang dihasilkan (di folder model/):
  - best_model.keras          <- Model dengan val_accuracy terbaik
  - final_model.keras         <- Model dari akhir training Phase 2
  - history_phase1_frozen.png <- Kurva akurasi/loss Phase 1
  - history_phase2_finetune.png <- Kurva akurasi/loss Phase 2
  - confusion_matrix.png      <- Confusion matrix test set
  - evaluation_report.txt     <- Classification report lengkap

Cara menjalankan (dari root folder project):
    (venv) python src/train.py
"""

import os
import sys
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend agar tidak perlu display
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from tensorflow.keras.callbacks import (
    ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
)

# ── Path otomatis berdasarkan lokasi file ini ──────────────────────────────
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from preprocessing import load_data, pair_images_with_symptoms
from model_fusion   import build_fusion_model, compile_model, unfreeze_for_finetuning


# =============================================================================
# KONFIGURASI TRAINING — Ubah nilai di sini jika perlu
# =============================================================================
BATCH_SIZE         = 16
EPOCHS_PHASE1      = 30       # Phase 1: backbone frozen
EPOCHS_PHASE2      = 20       # Phase 2: fine-tuning
VAL_SPLIT          = 0.10     # 10% dari data train untuk validasi internal

PATIENCE_EARLY_P1  = 8        # EarlyStopping patience Phase 1
PATIENCE_EARLY_P2  = 8        # EarlyStopping patience Phase 2
PATIENCE_LR        = 4        # ReduceLROnPlateau patience
LR_FACTOR          = 0.5      # Faktor pengurangan LR

# Jumlah layer backbone yang dibuka di Phase 2 (dari ujung, total ~155 layer)
NUM_UNFREEZE       = 30

CLASSES    = ['campak', 'rubella', 'cacar']
MODEL_DIR  = os.path.join(ROOT_DIR, 'model')
os.makedirs(MODEL_DIR, exist_ok=True)

SEED = 42
tf.random.set_seed(SEED)
np.random.seed(SEED)


# =============================================================================
# DATA AUGMENTATION ONLINE (hanya untuk data TRAIN via tf.data)
# =============================================================================
def augment_image(image):
    """
    Augmentasi online ringan pada citra saat training.
    Input sudah di-normalize [0,1]. Model akan menge-scale ulang ke [-1,1].
    """
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_flip_up_down(image)
    image = tf.image.random_brightness(image, max_delta=0.30)
    image = tf.image.random_contrast(image, lower=0.60, upper=1.40)
    image = tf.image.random_saturation(image, lower=0.60, upper=1.40)
    image = tf.image.random_hue(image, max_delta=0.1)
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image


# =============================================================================
# HELPER: BUAT tf.data.Dataset
# =============================================================================
def make_dataset(X_img, X_sym, y, batch_size: int, shuffle: bool = True,
                 augment: bool = False) -> tf.data.Dataset:
    """
    Membuat tf.data.Dataset yang efisien dengan prefetch.

    Args:
        X_img   : ndarray gambar (N, 224, 224, 3), float32 [0,1]
        X_sym   : ndarray gejala (N, 13), float32
        y       : ndarray label int64 (N,)
        shuffle : acak urutan data (True untuk train)
        augment : terapkan augmentasi online (True untuk train)
    """
    ds = tf.data.Dataset.from_tensor_slices(
        ({'input_citra': X_img, 'input_gejala': X_sym}, y)
    )
    if shuffle:
        ds = ds.shuffle(buffer_size=len(y), seed=SEED, reshuffle_each_iteration=True)
    if augment:
        def apply_aug(inputs, label):
            inputs['input_citra'] = augment_image(inputs['input_citra'])
            return inputs, label
        ds = ds.map(apply_aug, num_parallel_calls=tf.data.AUTOTUNE)
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)


# =============================================================================
# HELPER: VISUALISASI HISTORY
# =============================================================================
def plot_history(history, phase_name: str = 'phase'):
    """Simpan kurva akurasi dan loss ke file PNG."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Training History - {phase_name.replace("_", " ").title()}',
                 fontsize=14, fontweight='bold')

    # Accuracy
    ax1.plot(history.history['accuracy'],     label='Train', color='#4ECDC4', linewidth=2)
    ax1.plot(history.history['val_accuracy'], label='Validasi', color='#FF4B4B', linewidth=2, linestyle='--')
    ax1.set_title('Akurasi per Epoch')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1.05])

    # Loss
    ax2.plot(history.history['loss'],     label='Train', color='#4ECDC4', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Validasi', color='#FF4B4B', linewidth=2, linestyle='--')
    ax2.set_title('Loss per Epoch')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = os.path.join(MODEL_DIR, f'history_{phase_name}.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Grafik disimpan : {save_path}")


# =============================================================================
# HELPER: EVALUASI LENGKAP
# =============================================================================
def evaluate_and_report(model, ds_test, X_img_test, X_sym_test, y_test):
    """Evaluasi model pada test set dan simpan laporan + confusion matrix + metrics image."""
    print("\n" + "=" * 60)
    print("  EVALUASI AKHIR (TEST SET)")
    print("=" * 60)

    # Prediksi
    y_pred_prob = model.predict(
        {'input_citra': X_img_test, 'input_gejala': X_sym_test},
        verbose=1
    )
    y_pred = np.argmax(y_pred_prob, axis=1)

    # Metrik dari dataset TF (lebih akurat karena pakai loss yg sama saat training)
    test_loss, test_acc = model.evaluate(ds_test, verbose=0)
    print(f"\n  Test Loss        : {test_loss:.4f}")
    print(f"  Test Accuracy    : {test_acc:.4f}  ({test_acc * 100:.2f}%)")

    # Classification Report
    report = classification_report(y_test, y_pred, target_names=CLASSES, digits=4)
    report_dict = classification_report(y_test, y_pred, target_names=CLASSES, digits=4, output_dict=True)
    print("\n  Classification Report:")
    print(report)

    # Simpan ke file teks
    report_path = os.path.join(MODEL_DIR, 'evaluation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  HASIL EVALUASI MODEL FUSIONNET (MobileNetV2 + MLP)\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Test Loss        : {test_loss:.4f}\n")
        f.write(f"Test Accuracy    : {test_acc:.4f}  ({test_acc * 100:.2f}%)\n\n")
        f.write("Classification Report:\n")
        f.write(report)
    print(f"  Laporan evaluasi : {report_path}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=[c.capitalize() for c in CLASSES],
                yticklabels=[c.capitalize() for c in CLASSES],
                linewidths=0.5, annot_kws={"size": 14})
    ax.set_title('Confusion Matrix - Test Set', fontsize=13, fontweight='bold')
    ax.set_xlabel('Prediksi', fontsize=12)
    ax.set_ylabel('Aktual', fontsize=12)
    plt.tight_layout()
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Confusion matrix : {cm_path}")

    # ── METRICS REPORT IMAGE ──
    _generate_metrics_image(report_dict, test_acc, test_loss)

    return test_acc


def _generate_metrics_image(report_dict, test_acc, test_loss):
    """Generate gambar tabel metrik evaluasi: Accuracy, Precision, Recall, F1-Score."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    # Judul
    fig.suptitle('Laporan Evaluasi Model FusionNet',
                 fontsize=16, fontweight='bold', y=0.96, color='#1a1a2e')
    ax.text(0.5, 0.95, f'Overall Accuracy: {test_acc*100:.2f}%  |  Test Loss: {test_loss:.4f}',
            transform=ax.transAxes, ha='center', fontsize=12, color='#4a4a4a',
            style='italic')

    # Data tabel
    col_labels = ['Kelas', 'Precision', 'Recall', 'F1-Score', 'Support']
    table_data = []
    for cls in CLASSES:
        d = report_dict[cls]
        table_data.append([
            cls.capitalize(),
            f"{d['precision']:.4f}",
            f"{d['recall']:.4f}",
            f"{d['f1-score']:.4f}",
            f"{int(d['support'])}",
        ])

    # Tambah separator dan summary rows
    table_data.append(['', '', '', '', ''])  # blank row
    for key, label in [('macro avg', 'Macro Avg'), ('weighted avg', 'Weighted Avg')]:
        d = report_dict[key]
        table_data.append([
            label,
            f"{d['precision']:.4f}",
            f"{d['recall']:.4f}",
            f"{d['f1-score']:.4f}",
            f"{int(d['support'])}",
        ])

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
    )

    # Styling tabel
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 1.8)

    # Style header
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#0b4bcc')
        cell.set_text_props(color='white', fontweight='bold', fontsize=12)
        cell.set_edgecolor('#ffffff')

    # Style data rows
    for i in range(1, len(table_data) + 1):
        for j in range(len(col_labels)):
            cell = table[i, j]
            cell.set_edgecolor('#e0e0e0')
            if i <= len(CLASSES):
                # Per-class rows
                cell.set_facecolor('#f0f4ff' if i % 2 == 1 else '#ffffff')
            elif table_data[i-1][0] == '':
                # Blank separator row
                cell.set_facecolor('#ffffff')
                cell.set_edgecolor('#ffffff')
                cell.set_height(0.02)
            else:
                # Summary rows
                cell.set_facecolor('#e8f0fe')
                cell.set_text_props(fontweight='bold')

    plt.tight_layout()
    metrics_path = os.path.join(MODEL_DIR, 'metrics_report.png')
    plt.savefig(metrics_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Metrics report   : {metrics_path}")


# =============================================================================
# MAIN — ALUR TRAINING LENGKAP
# =============================================================================
def main():
    print("=" * 60)
    print("  TRAINING FUSIONNET — MobileNetV2 + MLP FUSION")
    print("  Klasifikasi Ruam Kulit: Campak | Rubella | Cacar Air")
    print("=" * 60)

    # ------------------------------------------------------------------
    # LANGKAH 1: Load dataset (citra dari folder + gejala dari CSV)
    # ------------------------------------------------------------------
    print("\n[1/7] Memuat dataset citra & gejala klinis...")
    data    = load_data(os.path.join(ROOT_DIR, 'data'))
    img_full = data['images']    # {'X_train', 'y_train', 'X_test', 'y_test'}
    sym_full = data['symptoms']  # {'X_train', 'y_train', 'X_test', 'y_test'}
    classes  = data['classes']

    print(f"\n  Citra  train : {img_full['X_train'].shape}")
    print(f"  Citra  test  : {img_full['X_test'].shape}")
    print(f"  Gejala train : {sym_full['X_train'].shape}")
    print(f"  Gejala test  : {sym_full['X_test'].shape}")

    # ------------------------------------------------------------------
    # LANGKAH 2: Pairing citra <-> gejala (per kelas, random sampling)
    # ------------------------------------------------------------------
    print("\n[2/7] Memasangkan citra dengan gejala per kelas...")
    X_img_tr_full, X_sym_tr_full, y_tr_full = pair_images_with_symptoms(
        img_full['X_train'], img_full['y_train'],
        sym_full['X_train'], sym_full['y_train'], seed=SEED
    )
    X_img_test, X_sym_test, y_test = pair_images_with_symptoms(
        img_full['X_test'], img_full['y_test'],
        sym_full['X_test'], sym_full['y_test'], seed=SEED + 1
    )
    print(f"  Pasangan train: {len(y_tr_full):,} | test: {len(y_test):,}")

    # ------------------------------------------------------------------
    # LANGKAH 3: Split folder test (20%) -> 10% Validasi + 10% Test murni
    # ------------------------------------------------------------------
    print(f"\n[3/7] Split test set menjadi validasi & test final (50/50)...")
    idx_val, idx_test = train_test_split(
        np.arange(len(y_test)),
        test_size=0.5,
        stratify=y_test,
        random_state=SEED
    )
    
    # Train = 100% dari folder train
    X_img_tr  = X_img_tr_full
    X_sym_tr  = X_sym_tr_full
    y_tr      = y_tr_full
    
    # Validation = 50% dari folder test
    X_img_val = X_img_test[idx_val]
    X_sym_val = X_sym_test[idx_val]
    y_val     = y_test[idx_val]
    
    # Test = 50% sisa dari folder test
    X_img_test_final = X_img_test[idx_test]
    X_sym_test_final = X_sym_test[idx_test]
    y_test_final     = y_test[idx_test]

    print(f"\n  Ringkasan data (80% Train, 10% Val, 10% Test):")
    print(f"    Train aktif  : {len(y_tr):,} sampel (Augmented)")
    print(f"    Validasi     : {len(y_val):,} sampel (Murni)")
    print(f"    Test         : {len(y_test_final):,} sampel (Murni)")
    print(f"    Total        : {len(y_tr) + len(y_val) + len(y_test_final):,} sampel")

    # ------------------------------------------------------------------
    # LANGKAH 4: Buat tf.data.Dataset (augmentasi online untuk train)
    # ------------------------------------------------------------------
    print("\n[4/7] Membuat tf.data pipeline (augmentasi online aktif untuk train)...")
    ds_train = make_dataset(X_img_tr,  X_sym_tr,  y_tr,  BATCH_SIZE, shuffle=True,  augment=True)
    ds_val   = make_dataset(X_img_val, X_sym_val, y_val, BATCH_SIZE, shuffle=False, augment=False)
    ds_test  = make_dataset(X_img_test_final, X_sym_test_final, y_test_final, BATCH_SIZE, shuffle=False, augment=False)

    # Class weights untuk menangani imbalance
    class_weights_arr = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(y_tr),
        y=y_tr
    )
    class_weight_dict = dict(enumerate(class_weights_arr))
    print(f"\n  Class weights (balance otomatis):")
    for idx, cls in enumerate(classes):
        print(f"    {cls:10s}: {class_weight_dict[idx]:.4f}")

    # ------------------------------------------------------------------
    # LANGKAH 5: Bangun model FusionNet baru
    # ------------------------------------------------------------------
    print("\n[5/7] Membangun model FusionNet (MobileNetV2 frozen + MLP)...")
    model = build_fusion_model()
    model = compile_model(model)
    print(f"  Arsitektur  : FusionNet_MobileNetV2_MLP")
    print(f"  Total param : {model.count_params():,}")
    print(f"  Input citra : {model.input_shape[0]}")
    print(f"  Input gejala: {model.input_shape[1]}")

    # ------------------------------------------------------------------
    # LANGKAH 6: PHASE 1 — Training head (backbone frozen)
    # ------------------------------------------------------------------
    best_model_path = os.path.join(MODEL_DIR, 'best_model.keras')
    print(f"\n[6/7] PHASE 1 - Training Head ({EPOCHS_PHASE1} epoch, backbone frozen)")
    print(f"  LR awal      : 1e-4")
    print(f"  Batch size   : {BATCH_SIZE}")
    print(f"  Checkpoint   : {best_model_path}")
    print("-" * 60)

    callbacks_p1 = [
        ModelCheckpoint(
            filepath=best_model_path,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1,
            mode='max'
        ),
        EarlyStopping(
            monitor='val_accuracy',
            patience=PATIENCE_EARLY_P1,
            restore_best_weights=True,
            verbose=1,
            mode='max'
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=LR_FACTOR,
            patience=PATIENCE_LR,
            min_lr=1e-7,
            verbose=1
        ),
    ]

    history_p1 = model.fit(
        ds_train,
        validation_data=ds_val,
        epochs=EPOCHS_PHASE1,
        callbacks=callbacks_p1,
        class_weight=class_weight_dict,
        verbose=1
    )
    plot_history(history_p1, phase_name='phase1_frozen')

    best_p1_acc = max(history_p1.history['val_accuracy'])
    print(f"\n  [Phase 1] Selesai. Best val_accuracy: {best_p1_acc:.4f} ({best_p1_acc*100:.2f}%)")

    # ------------------------------------------------------------------
    # LANGKAH 7: PHASE 2 — Fine-tuning MobileNetV2 (N layer terakhir)
    # ------------------------------------------------------------------
    print(f"\n[7/7] PHASE 2 - Fine-tuning ({EPOCHS_PHASE2} epoch, {NUM_UNFREEZE} layer backbone dibuka)")
    print(f"  LR fine-tune : 1e-5 (10x lebih kecil dari Phase 1)")
    print("-" * 60)

    model = unfreeze_for_finetuning(model, num_layers_to_unfreeze=NUM_UNFREEZE)

    callbacks_p2 = [
        ModelCheckpoint(
            filepath=best_model_path,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1,
            mode='max'
        ),
        EarlyStopping(
            monitor='val_accuracy',
            patience=PATIENCE_EARLY_P2,
            restore_best_weights=True,
            verbose=1,
            mode='max'
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=LR_FACTOR,
            patience=PATIENCE_LR,
            min_lr=1e-8,
            verbose=1
        ),
    ]

    history_p2 = model.fit(
        ds_train,
        validation_data=ds_val,
        epochs=EPOCHS_PHASE2,
        callbacks=callbacks_p2,
        class_weight=class_weight_dict,
        verbose=1
    )
    plot_history(history_p2, phase_name='phase2_finetune')

    best_p2_acc = max(history_p2.history['val_accuracy'])
    print(f"\n  [Phase 2] Selesai. Best val_accuracy: {best_p2_acc:.4f} ({best_p2_acc*100:.2f}%)")

    # ------------------------------------------------------------------
    # EVALUASI FINAL pada test set
    # ------------------------------------------------------------------
    print("\nMemuat model terbaik dari checkpoint untuk evaluasi...")
    best_model = tf.keras.models.load_model(best_model_path)
    final_test_acc = evaluate_and_report(best_model, ds_test, X_img_test_final, X_sym_test_final, y_test_final)

    # ------------------------------------------------------------------
    # SIMPAN MODEL FINAL
    # ------------------------------------------------------------------
    final_path = os.path.join(MODEL_DIR, 'final_model.keras')
    best_model.save(final_path)
    print("Model final berhasil disimpan di : " + final_path)
    print("Model klasifikasi berhasil disimpan.")

    # ------------------------------------------------------------------
    # RINGKASAN AKHIR
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  TRAINING SELESAI!")
    print("=" * 60)
    print(f"  Best val_accuracy Phase 1 : {best_p1_acc*100:.2f}%")
    print(f"  Best val_accuracy Phase 2 : {best_p2_acc*100:.2f}%")
    print(f"  Test Accuracy (final)     : {final_test_acc*100:.2f}%")
    print(f"\n  Output tersimpan di: {MODEL_DIR}")
    print(f"    - best_model.keras")
    print(f"    - final_model.keras")
    print(f"    - scaler.pkl")
    print(f"    - history_phase1_frozen.png")
    print(f"    - history_phase2_finetune.png")
    print(f"    - confusion_matrix.png")
    print(f"    - evaluation_report.txt")
    print("=" * 60)


if __name__ == '__main__':
    main()
