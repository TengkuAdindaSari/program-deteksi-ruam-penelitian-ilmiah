"""
augmentasi.py
=============
Augmentasi citra: setiap gambar asli menghasilkan 15 variasi baru.
Berlaku untuk SEMUA kelas (campak, rubella, cacar) di folder TRAIN saja
(sesuai skema split 80/20 — augmentasi tidak boleh masuk ke folder test).

Struktur folder yang diharapkan (skema 80/20, hanya 2 split):
    data/images/<kelas>/train/
    data/images/<kelas>/test/

Letakkan file ini di: src/augmentasi.py
Jalankan dari ROOT folder:
    (venv) python src/augmentasi.py
"""

import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import random

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# PATH OTOMATIS
# ─────────────────────────────────────────────
SRC_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SRC_DIR)
IMAGE_BASE = os.path.join(ROOT_DIR, 'data', 'images')

print(f"Root folder : {ROOT_DIR}")
print(f"Image folder: {IMAGE_BASE}")

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
CLASSES        = ['campak', 'rubella', 'cacar']
TARGET_SPLIT   = 'train'        # augmentasi hanya pada folder train
AUG_PER_IMAGE  = 15
VALID_EXT      = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


# ─────────────────────────────────────────────
# TEKNIK AUGMENTASI
# ─────────────────────────────────────────────
def flip_horizontal(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def flip_vertical(img):
    return img.transpose(Image.FLIP_TOP_BOTTOM)

def rotate(img, angle):
    return img.rotate(angle, expand=False, fillcolor=(200, 200, 200))

def brightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def contrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def saturation(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def sharpness(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def zoom_in(img, zoom):
    w, h = img.size
    left = int(w * (1 - zoom) / 2)
    top  = int(h * (1 - zoom) / 2)
    return img.crop((left, top, w - left, h - top)).resize((w, h), Image.LANCZOS)

def blur_img(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

def noise(img, intensity):
    arr = np.array(img, dtype=np.int16)
    n   = np.random.randint(-intensity, intensity, arr.shape, dtype=np.int16)
    return Image.fromarray(np.clip(arr + n, 0, 255).astype(np.uint8))

def translate(img, dx, dy):
    return img.transform(img.size, Image.AFFINE,
                         (1, 0, dx, 0, 1, dy),
                         fillcolor=(200, 200, 200))


# ─── 15 RESEP AUGMENTASI (1 resep = 1 gambar baru per gambar asli) ───
RECIPES = [
    [lambda img: flip_horizontal(img)],
    [lambda img: flip_vertical(img)],
    [lambda img: brightness(flip_horizontal(img), 1.3)],
    [lambda img: brightness(flip_horizontal(img), 0.7)],
    [lambda img: rotate(img, -15)],
    [lambda img: rotate(img, 15)],
    [lambda img: rotate(img, -25)],
    [lambda img: rotate(img, 25)],
    [lambda img: flip_horizontal(rotate(img, 10))],
    [lambda img: zoom_in(img, 0.85)],
    [lambda img: zoom_in(img, 0.80)],
    [lambda img: brightness(zoom_in(img, 0.85), 1.2)],
    [lambda img: contrast(img, 1.4)],
    [lambda img: saturation(img, 1.5)],
    [lambda img: blur_img(img, 1.0)],
]

assert len(RECIPES) == AUG_PER_IMAGE, \
    f"Jumlah resep ({len(RECIPES)}) harus = AUG_PER_IMAGE ({AUG_PER_IMAGE})"


def apply_recipe(img, recipe):
    result = img.copy()
    for fn in recipe:
        result = fn(result)
    return result


def augment_folder(cls, split):
    """Augmentasi semua gambar asli di folder data/images/<cls>/<split>/."""
    folder = os.path.join(IMAGE_BASE, cls, split)

    if not os.path.exists(folder):
        print(f"\n  [ERROR] Folder tidak ditemukan: {folder}")
        return 0, 0

    originals = [
        f for f in sorted(os.listdir(folder))
        if os.path.splitext(f)[1].lower() in VALID_EXT
        and not f.startswith('aug_')
    ]

    if not originals:
        print(f"\n  [SKIP] Tidak ada gambar asli di: {folder}")
        return 0, 0

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
    return len(originals), generated


def cek_distribusi():
    print("\n--- Distribusi Dataset Sekarang (80/20) ---")
    print(f"{'Kelas':<12} {'Train':>10} {'Test':>10} {'Total':>10}")
    print("-" * 46)
    grand_total = 0
    for cls in CLASSES:
        counts = {}
        for split in ['train', 'test']:
            folder = os.path.join(IMAGE_BASE, cls, split)
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder)
                         if os.path.splitext(f)[1].lower() in VALID_EXT]
                counts[split] = len(files)
            else:
                counts[split] = 0
        total = counts.get('train', 0) + counts.get('test', 0)
        grand_total += total
        print(f"{cls:<12} {counts.get('train',0):>10} {counts.get('test',0):>10} {total:>10}")
    print("-" * 46)
    print(f"{'TOTAL':<12} {'':>10} {'':>10} {grand_total:>10}")


if __name__ == '__main__':
    print("=" * 55)
    print("  AUGMENTASI DATASET - 15 variasi per gambar asli")
    print("  (Hanya folder TRAIN - skema split 80/20)")
    print("=" * 55)

    summary = []
    for cls in CLASSES:
        print(f"\n Kelas: {cls.upper()}")
        asli, aug = augment_folder(cls, TARGET_SPLIT)
        summary.append((cls, asli, aug))

    print("\n--- Ringkasan Augmentasi ---")
    for cls, asli, aug in summary:
        print(f"  {cls:10s}: {asli} asli -> +{aug} augmentasi -> {asli+aug} total di train/")

    cek_distribusi()
