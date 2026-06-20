"""
split_dataset.py
================
Membagi dataset citra asli dari folder:
    - data/images/Campak
    - data/images/Rubella
    - data/images/Cacar Air
Menjadi split 80% train dan 20% test ke folder:
    - data/images/campak/train/ dan data/images/campak/test/
    - data/images/rubella/train/ dan data/images/rubella/test/
    - data/images/cacar/train/ dan data/images/cacar/test/

Jalankan dari ROOT folder:
    (venv) python src/split_dataset.py
"""

import os
import shutil
import random

# Seed agar hasil split konsisten (reproducible)
random.seed(42)

# Path otomatis
SRC_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SRC_DIR)
IMAGE_BASE = os.path.join(ROOT_DIR, 'data', 'images')

# Mapping folder sumber ke target kelas
CLASS_MAP = {
    'Campak': 'campak',
    'Rubella': 'rubella',
    'Cacar Air': 'cacar'
}

VALID_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def split_data():
    print("=" * 60)
    # Cek apakah folder asal ada
    for src_name in CLASS_MAP.keys():
        src_path = os.path.join(IMAGE_BASE, src_name)
        if not os.path.exists(src_path):
            print(f"[ERROR] Folder sumber '{src_path}' tidak ditemukan!")
            print("Pastikan folder dataset 'Campak', 'Rubella', dan 'Cacar Air' ada di data/images/")
            return

    print("Memulai pembagian dataset (80% Train, 20% Test)...")
    print("=" * 60)

    for src_name, dest_name in CLASS_MAP.items():
        src_path = os.path.join(IMAGE_BASE, src_name)
        
        # Buat folder train dan test tujuan
        train_path = os.path.join(IMAGE_BASE, dest_name, 'train')
        test_path = os.path.join(IMAGE_BASE, dest_name, 'test')
        
        os.makedirs(train_path, exist_ok=True)
        os.makedirs(test_path, exist_ok=True)
        
        # Ambil semua file gambar valid
        all_files = [
            f for f in os.listdir(src_path)
            if os.path.splitext(f)[1].lower() in VALID_EXT
        ]
        
        # Acak file
        random.shuffle(all_files)
        
        # Tentukan batas split 80/20
        split_idx = int(len(all_files) * 0.8)
        train_files = all_files[:split_idx]
        test_files = all_files[split_idx:]
        
        print(f"\nKelas: {src_name} -> {dest_name}")
        print(f"  Total gambar asli : {len(all_files)}")
        print(f"  Jumlah ke train/  : {len(train_files)} (80%)")
        print(f"  Jumlah ke test/   : {len(test_files)} (20%)")
        
        # Copy file ke train
        for fname in train_files:
            shutil.copy2(os.path.join(src_path, fname), os.path.join(train_path, fname))
            
        # Copy file ke test
        for fname in test_files:
            shutil.copy2(os.path.join(src_path, fname), os.path.join(test_path, fname))
            
    print("\n" + "=" * 60)
    print("Dataset berhasil dibagi!")
    print("Sekarang Anda bisa menjalankan augmentasi:")
    print("  python src/augmentasi.py")
    print("=" * 60)

if __name__ == '__main__':
    split_data()
