"""
augmentasi.py
=============
Membuat 15 variasi augmentasi untuk setiap gambar asli rubella.

Hasil: 32 gambar asli x 15 augmentasi = 480 gambar baru
       Total folder training = 512 gambar

Letakkan file ini di: src\augmentasi.py
Jalankan dari ROOT folder:
    (venv) D:\program pi> python src\augmentasi.py
"""

import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import random

# ─────────────────────────────────────────────
# PATH OTOMATIS
# Naik satu level dari src\ ke root folder
# ─────────────────────────────────────────────
SRC_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SRC_DIR)
IMAGE_BASE = os.path.join(ROOT_DIR, 'data', 'images')

print(f"Root folder : {ROOT_DIR}")
print(f"Image folder: {IMAGE_BASE}")

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
TARGET        = {'rubella': ['training']}
AUG_PER_IMAGE = 15
VALID_EXT     = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


# ─────────────────────────────────────────────
# TEKNIK AUGMENTASI
# ─────────────────────────────────────────────
def flip_horizontal(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def rotate(img, angle=None):
    if angle is None:
        angle = random.uniform(-25, 25)
    return img.rotate(angle, expand=False, fillcolor=(200, 200, 200))

def brightness(img, factor=None):
    factor = factor or random.uniform(0.6, 1.4)
    return ImageEnhance.Brightness(img).enhance(factor)

def contrast(img, factor=None):
    factor = factor or random.uniform(0.6, 1.4)
    return ImageEnhance.Contrast(img).enhance(factor)

def saturation(img, factor=None):
    factor = factor or random.uniform(0.5, 1.5)
    return ImageEnhance.Color(img).enhance(factor)

def zoom_in(img, zoom=None):
    w, h = img.size
    zoom = zoom or random.uniform(0.75, 0.92)
    left = int(w * (1 - zoom) / 2)
    top  = int(h * (1 - zoom) / 2)
    return img.crop((left, top, w - left, h - top)).resize((w, h), Image.LANCZOS)

def blur_img(img):
    return img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.8)))

def sharpen(img, factor=None):
    factor = factor or random.uniform(1.5, 3.0)
    return ImageEnhance.Sharpness(img).enhance(factor)

def noise(img, intensity=None):
    intensity = intensity or random.randint(8, 25)
    arr = np.array(img, dtype=np.int16)
    n   = np.random.randint(-intensity, intensity, arr.shape, dtype=np.int16)
    return Image.fromarray(np.clip(arr + n, 0, 255).astype(np.uint8))

def translate(img):
    w, h = img.size
    dx   = random.randint(-int(w * 0.1), int(w * 0.1))
    dy   = random.randint(-int(h * 0.1), int(h * 0.1))
    return img.transform(img.size, Image.AFFINE,
                         (1, 0, dx, 0, 1, dy),
                         fillcolor=(200, 200, 200))

RECIPES = [
    [flip_horizontal],
    [flip_horizontal, lambda img: brightness(img, 1.3)],
    [flip_horizontal, lambda img: brightness(img, 0.7)],
    [lambda img: rotate(img, -15)],
    [lambda img: rotate(img, 15)],
    [lambda img: rotate(img, 10), flip_horizontal],
    [lambda img: zoom_in(img, 0.85)],
    [lambda img: zoom_in(img, 0.80), lambda img: brightness(img, 1.2)],
    [lambda img: contrast(img, 1.4)],
    [lambda img: contrast(img, 0.7)],
    [lambda img: saturation(img, 1.5)],
    [blur_img, flip_horizontal],
    [noise, lambda img: brightness(img, 1.1)],
    [translate, lambda img: rotate(img, 8)],
    [sharpen, flip_horizontal, lambda img: zoom_in(img, 0.90)],
]


# ─────────────────────────────────────────────
# FUNGSI UTAMA
# ─────────────────────────────────────────────
def apply_recipe(img, recipe):
    result = img.copy()
    for fn in recipe:
        result = fn(result)
    return result


def augment_folder(cls, split):
    folder = os.path.join(IMAGE_BASE, cls, split)

    if not os.path.exists(folder):
        print(f"\n  [ERROR] Folder tidak ditemukan: {folder}")
        return

    originals = [
        f for f in sorted(os.listdir(folder))
        if os.path.splitext(f)[1].lower() in VALID_EXT
        and not f.startswith('aug_')
    ]

    if not originals:
        print(f"\n  [SKIP] Tidak ada gambar asli di: {folder}")
        return

    total_baru = len(originals) * AUG_PER_IMAGE
    print(f"\n  Folder  : {folder}")
    print(f"  Asli    : {len(originals)} gambar")
    print(f"  Tambahan: {len(originals)} x {AUG_PER_IMAGE} = {total_baru} gambar")
    print(f"  Total   : {len(originals) + total_baru} gambar")
    print(f"  Proses  : ", end='', flush=True)

    generated = 0
    for fname in originals:
        fpath = os.path.join(folder, fname)
        stem  = os.path.splitext(fname)[0]
        try:
            img = Image.open(fpath).convert('RGB')
        except Exception as e:
            print(f"\n  [ERROR] {fpath}: {e}")
            continue

        for i, recipe in enumerate(RECIPES):
            try:
                aug      = apply_recipe(img, recipe)
                out_name = f"aug_{stem}_{i + 1:02d}.jpg"
                out_path = os.path.join(folder, out_name)
                aug.save(out_path, 'JPEG', quality=92)
                generated += 1
            except Exception as e:
                print(f"\n  [ERROR] Resep {i+1} untuk {fname}: {e}")

        print('.', end='', flush=True)

    print(" selesai!")
    print(f"  Berhasil membuat {generated} gambar baru")


def cek_distribusi():
    print("\n─── Distribusi Dataset Sekarang ───")
    print(f"{'Kelas':<12} {'Training':>10} {'Validasi':>10} {'Test':>8}")
    print("-" * 45)
    for cls in ['campak', 'rubella', 'cacar']:
        counts = {}
        for split in ['training', 'validasi', 'test']:
            folder = os.path.join(IMAGE_BASE, cls, split)
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder)
                         if os.path.splitext(f)[1].lower() in VALID_EXT]
                counts[split] = len(files)
            else:
                counts[split] = 0
        print(f"{cls:<12} {counts.get('training',0):>10} "
              f"{counts.get('validasi',0):>10} {counts.get('test',0):>8}")


if __name__ == '__main__':
    print("=" * 55)
    print("  AUGMENTASI DATASET — 15 variasi per gambar asli")
    print("=" * 55)

    for cls, splits in TARGET.items():
        print(f"\n Kelas: {cls.upper()}")
        for split in splits:
            augment_folder(cls, split)

    cek_distribusi()