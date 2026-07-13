"""
preprocessing.py
================
Preprocessing data citra (CNN) DAN gejala klinis (MLP) untuk
klasifikasi penyakit ruam kulit: campak, rubella, cacar.
Skema split: 80% train, 20% test (validasi diambil otomatis
dari 10% bagian train saat training).

Struktur folder yang diharapkan:
    data/
    ├── images/
    │   ├── campak/
    │   │   ├── train/   (80%, termasuk hasil augmentasi)
    │   │   └── test/    (20%, gambar asli saja)
    │   ├── rubella/
    │   │   ├── train/
    │   │   └── test/
    │   └── cacar/
    │       ├── train/
    │       └── test/
    └── symptoms.csv
"""

import os
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


# ─────────────────────────────────────────────
# KONFIGURASI — PATH OTOMATIS
# ─────────────────────────────────────────────
IMG_SIZE = (224, 224)

_SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SRC_DIR)

DATA_PATH   = os.path.join(_ROOT_DIR, 'data')
IMAGE_PATH  = os.path.join(DATA_PATH, 'images')
SYMPTOM_CSV = os.path.join(DATA_PATH, 'symptoms.csv')

# Urutan ini MENENTUKAN label integer: campak=0, rubella=1, cacar=2
# JANGAN diubah urutannya setelah training!
CLASSES = ['campak', 'rubella', 'cacar']
SPLITS  = ['train', 'test']

VALID_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

# Kolom fitur gejala klinis (10 fitur, setelah durasi_demam dan pilek dihapus)
SYMPTOM_FEATURES = [
    'demam_tinggi', 'demam_ringan',
    'koplik_spot', 'kelenjar_bengkak', 'vesikel',
    'konjungtivitis', 'nyeri_sendi', 'sakit_tenggorokan',
    'lemas_malaise', 'pola_ruam'
]


# ─────────────────────────────────────────────
# 1. PREPROCESSING CITRA
# ─────────────────────────────────────────────

def load_image(filepath: str, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """Baca 1 gambar, resize, normalisasi piksel ke [0, 1]."""
    img = Image.open(filepath).convert('RGB').resize(img_size)
    return np.array(img, dtype=np.float32) / 255.0


def load_images_from_split(split: str) -> tuple:
    """
    Memuat semua citra dari satu split (train/test) untuk semua kelas.

    Return:
        X : np.ndarray shape (N, 224, 224, 3)
        y : np.ndarray shape (N,) label integer
        filenames : list nama file (untuk pencocokan urutan, opsional)
    """
    X, y = [], []
    class_to_idx = {cls: idx for idx, cls in enumerate(CLASSES)}

    for cls in CLASSES:
        folder = os.path.join(IMAGE_PATH, cls, split)
        if not os.path.exists(folder):
            print(f"[WARNING] Folder tidak ditemukan: {folder}")
            continue

        files = [f for f in os.listdir(folder)
                 if os.path.splitext(f)[1].lower() in VALID_EXT]
        print(f"  [{split}] {cls}: {len(files)} gambar ditemukan")

        for fname in files:
            fpath = os.path.join(folder, fname)
            try:
                X.append(load_image(fpath))
                y.append(class_to_idx[cls])
            except Exception as e:
                print(f"  [ERROR] Gagal membaca {fpath}: {e}")

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    return X, y


def load_all_images() -> dict:
    """Memuat citra dari train dan test (skema 80/20)."""
    print("=== Memuat data citra (skema 80/20) ===")
    X_train, y_train = load_images_from_split('train')
    print(f"  -> X_train: {X_train.shape}, y_train: {y_train.shape}")
    X_test, y_test = load_images_from_split('test')
    print(f"  -> X_test : {X_test.shape}, y_test : {y_test.shape}")
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_test' : X_test,  'y_test' : y_test,
    }


# ─────────────────────────────────────────────
# 2. PREPROCESSING GEJALA KLINIS
# ─────────────────────────────────────────────

def load_symptoms(csv_path: str = None) -> tuple:
    """
    Membaca symptoms.csv, memisahkan fitur & label.

    Return:
        X_sym : np.ndarray shape (N, 10)
        y     : np.ndarray shape (N,) label integer
    """
    csv_path = csv_path or SYMPTOM_CSV
    print("\n=== Memuat data gejala klinis ===")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"File tidak ditemukan: {csv_path}\nPastikan symptoms.csv ada di folder data/"
        )

    df = pd.read_csv(csv_path)
    print(f"  Total baris: {len(df)}")
    print(f"  Kolom      : {list(df.columns)}")

    missing = [c for c in SYMPTOM_FEATURES + ['label'] if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom berikut tidak ada di CSV: {missing}")

    X_sym = df[SYMPTOM_FEATURES].values.astype(np.float32)
    y_raw = df['label'].values

    class_to_idx = {cls: idx for idx, cls in enumerate(CLASSES)}
    y = np.array([class_to_idx[label] for label in y_raw], dtype=np.int64)

    print(f"  Distribusi kelas: {dict(zip(*np.unique(y_raw, return_counts=True)))}")
    return X_sym, y


def split_symptoms(X_sym: np.ndarray, y: np.ndarray,
                    test_size: float = 0.2, random_state: int = 42) -> dict:
    """Membagi data gejala menjadi train (80%) / test (20%)."""
    X_train, X_test, y_train, y_test = train_test_split(
        X_sym, y, test_size=test_size, stratify=y, random_state=random_state
    )
    print(f"\n  Split gejala -> train:{len(X_train)} | test:{len(X_test)}")
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_test' : X_test,  'y_test' : y_test,
    }


# ─────────────────────────────────────────────
# 3. FUNGSI UTAMA: LOAD SEMUA DATA
# ─────────────────────────────────────────────

def load_data(data_path: str = None) -> dict:
    """
    Fungsi utama — load citra & gejala, kembalikan dict siap pakai.
    """
    global DATA_PATH, IMAGE_PATH, SYMPTOM_CSV
    if data_path:
        DATA_PATH   = data_path
        IMAGE_PATH  = os.path.join(data_path, 'images')
        SYMPTOM_CSV = os.path.join(data_path, 'symptoms.csv')

    img_data       = load_all_images()
    X_sym, y       = load_symptoms()
    sym_data       = split_symptoms(X_sym, y)

    print("\n[OK] Preprocessing selesai!")
    return {
        'images'  : img_data,
        'symptoms': sym_data,
        'classes' : CLASSES,
    }


def pair_images_with_symptoms(X_img, y_img, X_sym, y_sym, seed=42):
    """
    Memasangkan citra dengan vektor gejala SECARA ACAK namun TETAP
    SEKELAS (label sama), karena jumlah baris kedua modalitas berbeda.

    Untuk setiap citra, dipilih satu baris gejala acak dari kelas yang sama.

    Return:
        X_img (tidak berubah), X_sym_paired (N_img, n_fitur), y (N_img,)
    """
    rng = np.random.default_rng(seed)
    X_sym_paired = np.zeros((len(y_img), X_sym.shape[1]), dtype=np.float32)

    for cls in np.unique(y_img):
        idx_img = np.where(y_img == cls)[0]
        idx_sym = np.where(y_sym == cls)[0]
        if len(idx_sym) == 0:
            raise ValueError(f"Tidak ada data gejala untuk kelas {cls}")
        chosen = rng.choice(idx_sym, size=len(idx_img), replace=True)
        X_sym_paired[idx_img] = X_sym[chosen]

    return X_img, X_sym_paired, y_img


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == '__main__':
    data = load_data()

    print("\n─── Ringkasan Data Citra ───")
    for cls in CLASSES:
        idx = CLASSES.index(cls)
        n_train = int(np.sum(data['images']['y_train'] == idx))
        n_test  = int(np.sum(data['images']['y_test']  == idx))
        print(f"  {cls:10s} | train: {n_train:4d} | test: {n_test:4d}")

    print("\n─── Ringkasan Data Gejala ───")
    for cls in CLASSES:
        idx = CLASSES.index(cls)
        n_train = int(np.sum(data['symptoms']['y_train'] == idx))
        n_test  = int(np.sum(data['symptoms']['y_test']  == idx))
        print(f"  {cls:10s} | train: {n_train:4d} | test: {n_test:4d}")
