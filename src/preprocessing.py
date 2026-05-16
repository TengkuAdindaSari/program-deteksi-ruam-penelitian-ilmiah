"""
preprocessing.py
================
Memuat dan mempersiapkan data citra serta gejala klinis
untuk klasifikasi penyakit ruam kulit (Campak, Rubella, Cacar Air).

Struktur folder yang diharapkan:
    data/
    ├── images/
    │   ├── campak/
    │   │   ├── training/
    │   │   ├── validasi/
    │   │   └── test/
    │   ├── rubella/
    │   │   ├── training/
    │   │   ├── validasi/
    │   │   └── test/
    │   └── cacar/
    │       ├── training/
    │       ├── validasi/
    │       └── test/
    └── symptoms.csv
"""

import os
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
IMG_SIZE    = (224, 224)      # ukuran input CNN (tinggi x lebar)
DATA_PATH   = 'data/'         # root folder data
IMAGE_PATH  = os.path.join(DATA_PATH, 'images')
SYMPTOM_CSV = os.path.join(DATA_PATH, 'symptoms.csv')

CLASSES = ['campak', 'rubella', 'cacar']   # nama folder = nama kelas
SPLITS  = ['training', 'validasi', 'test'] # nama subfolder


# ─────────────────────────────────────────────
# 1. PREPROCESSING CITRA
# ─────────────────────────────────────────────

def load_image(filepath: str, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """
    Membaca satu file gambar, resize, dan normalisasi piksel ke [0, 1].

    Parameter:
        filepath  : path ke file gambar (.jpg / .png)
        img_size  : tuple (lebar, tinggi), default (224, 224)

    Return:
        np.ndarray shape (H, W, 3), dtype float32
    """
    img = Image.open(filepath).convert('RGB')   # pastikan 3 channel
    img = img.resize(img_size)
    img_array = np.array(img, dtype=np.float32) / 255.0
    return img_array


def load_images_from_split(split: str) -> tuple:
    """
    Memuat semua citra dari satu split (training / validasi / test)
    untuk semua kelas.

    Parameter:
        split : 'training', 'validasi', atau 'test'

    Return:
        X : np.ndarray shape (N, 224, 224, 3)
        y : np.ndarray shape (N,) berisi label integer
    """
    X, y = [], []
    label_encoder = LabelEncoder()
    label_encoder.fit(CLASSES)

    valid_ext = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    for cls in CLASSES:
        folder = os.path.join(IMAGE_PATH, cls, split)

        if not os.path.exists(folder):
            print(f"[WARNING] Folder tidak ditemukan: {folder}")
            continue

        files = [f for f in os.listdir(folder)
                 if os.path.splitext(f)[1].lower() in valid_ext]

        print(f"  [{split}] {cls}: {len(files)} gambar ditemukan")

        for fname in files:
            fpath = os.path.join(folder, fname)
            try:
                img = load_image(fpath)
                X.append(img)
                y.append(cls)
            except Exception as e:
                print(f"  [ERROR] Gagal membaca {fpath}: {e}")

    X = np.array(X, dtype=np.float32)
    y = label_encoder.transform(y)
    return X, y


def load_all_images() -> dict:
    """
    Memuat citra dari semua split sekaligus.

    Return:
        dict berisi:
            'X_train', 'y_train'
            'X_val',   'y_val'
            'X_test',  'y_test'
    """
    print("=== Memuat data citra ===")
    split_map = {
        'training' : ('X_train', 'y_train'),
        'validasi'  : ('X_val',   'y_val'),
        'test'      : ('X_test',  'y_test'),
    }

    result = {}
    for split, (x_key, y_key) in split_map.items():
        X, y = load_images_from_split(split)
        result[x_key] = X
        result[y_key] = y
        print(f"  → {x_key}: {X.shape}, {y_key}: {y.shape}")

    return result


# ─────────────────────────────────────────────
# 2. PREPROCESSING GEJALA KLINIS
# ─────────────────────────────────────────────

def load_symptoms(csv_path: str = SYMPTOM_CSV) -> tuple:
    """
    Membaca symptoms.csv, memisahkan fitur dan label,
    lalu melakukan encoding label dan normalisasi fitur numerik.

    Kolom yang diharapkan di CSV:
        label           : nama penyakit (campak / rubella / cacar)
        durasi_demam    : jumlah hari demam (numerik)
        batuk           : 0 atau 1
        mata_merah      : 0 atau 1
        kelenjar_bengkak: 0 atau 1
        pola_ruam       : 0 atau 1  (menyebar wajah→badan)
        vesikel         : 0 atau 1  (ruam berisi cairan)

    Return:
        X_sym : np.ndarray shape (N, 6), fitur gejala
        y     : np.ndarray shape (N,),   label integer
        scaler: StandardScaler yang sudah di-fit (simpan untuk inferensi)
        le    : LabelEncoder yang sudah di-fit
    """
    print("\n=== Memuat data gejala klinis ===")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"File tidak ditemukan: {csv_path}\n"
            "Pastikan symptoms.csv ada di folder data/"
        )

    df = pd.read_csv(csv_path)
    print(f"  Total baris: {len(df)}")
    print(f"  Kolom      : {list(df.columns)}")

    # Pisahkan fitur dan label
    feature_cols = ['durasi_demam', 'batuk', 'mata_merah',
                    'kelenjar_bengkak', 'pola_ruam', 'vesikel']

    # Validasi kolom
    missing = [c for c in feature_cols + ['label'] if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom berikut tidak ada di CSV: {missing}")

    X_sym = df[feature_cols].values.astype(np.float32)
    y_raw = df['label'].values

    # Normalisasi fitur numerik (durasi_demam)
    scaler = StandardScaler()
    X_sym[:, 0] = scaler.fit_transform(X_sym[:, 0].reshape(-1, 1)).ravel()

    # Encode label
    le = LabelEncoder()
    le.fit(CLASSES)
    y = le.transform(y_raw)

    print(f"  Distribusi kelas: {dict(zip(*np.unique(y_raw, return_counts=True)))}")
    return X_sym, y, scaler, le


def split_symptoms(X_sym: np.ndarray, y: np.ndarray,
                   test_size: float = 0.1,
                   val_size: float  = 0.1,
                   random_state: int = 42) -> dict:
    """
    Membagi data gejala menjadi train / validasi / test.

    Return:
        dict berisi X_train, X_val, X_test, y_train, y_val, y_test
    """
    X_temp, X_test, y_temp, y_test = train_test_split(
        X_sym, y, test_size=test_size, stratify=y,
        random_state=random_state
    )
    val_ratio = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, stratify=y_temp,
        random_state=random_state
    )
    print(f"\n  Split gejala → train:{len(X_train)} | val:{len(X_val)} | test:{len(X_test)}")
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val'  : X_val,   'y_val'  : y_val,
        'X_test' : X_test,  'y_test' : y_test,
    }


# ─────────────────────────────────────────────
# 3. FUNGSI UTAMA: LOAD SEMUA DATA
# ─────────────────────────────────────────────

def load_data(data_path: str = DATA_PATH) -> dict:
    """
    Fungsi utama — memanggil semua preprocessing dan
    mengembalikan satu dict berisi data siap pakai.

    Return:
        {
          'images' : { X_train, y_train, X_val, y_val, X_test, y_test },
          'symptoms': { X_train, y_train, X_val, y_val, X_test, y_test },
          'scaler'  : StandardScaler (simpan untuk inferensi),
          'encoder' : LabelEncoder  (simpan untuk inferensi),
          'classes' : ['campak', 'rubella', 'cacar']
        }
    """
    global DATA_PATH, IMAGE_PATH, SYMPTOM_CSV
    DATA_PATH   = data_path
    IMAGE_PATH  = os.path.join(data_path, 'images')
    SYMPTOM_CSV = os.path.join(data_path, 'symptoms.csv')

    img_data             = load_all_images()
    X_sym, y, scaler, le = load_symptoms()
    sym_data             = split_symptoms(X_sym, y)

    print("\n✅ Preprocessing selesai!")
    return {
        'images'  : img_data,
        'symptoms': sym_data,
        'scaler'  : scaler,
        'encoder' : le,
        'classes' : CLASSES,
    }


# ─────────────────────────────────────────────
# QUICK TEST — jalankan langsung untuk verifikasi
# ─────────────────────────────────────────────
if __name__ == '__main__':
    data = load_data()

    print("\n─── Ringkasan Data ───")
    for split in ['X_train', 'X_val', 'X_test']:
        img  = data['images'][split]
        sym  = data['symptoms'][split]
        print(f"  {split:10s} | citra: {img.shape} | gejala: {sym.shape}")