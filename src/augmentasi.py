"""
augmentasi.py
=============
Membuat 30 variasi augmentasi untuk setiap gambar asli rubella.

Hasil: 18 gambar asli × 30 augmentasi = 540 gambar baru
       Total folder training = 18 + 540 = 558 gambar

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
AUG_PER_IMAGE = 30
VALID_EXT     = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


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


# ─── 30 RESEP AUGMENTASI ───
RECIPES = [
    # 1  — flip horizontal
    [lambda img: flip_horizontal(img)],
    # 2  — flip vertikal
    [lambda img: flip_vertical(img)],
    # 3  — flip H + terang
    [lambda img: brightness(flip_horizontal(img), 1.3)],
    # 4  — flip H + gelap
    [lambda img: brightness(flip_horizontal(img), 0.7)],
    # 5  — rotasi -15
    [lambda img: rotate(img, -15)],
    # 6  — rotasi +15
    [lambda img: rotate(img, 15)],
    # 7  — rotasi -25
    [lambda img: rotate(img, -25)],
    # 8  — rotasi +25
    [lambda img: rotate(img, 25)],
    # 9  — rotasi + flip H
    [lambda img: flip_horizontal(rotate(img, 10))],
    # 10 — zoom 85%
    [lambda img: zoom_in(img, 0.85)],
    # 11 — zoom 80%
    [lambda img: zoom_in(img, 0.80)],
    # 12 — zoom + terang
    [lambda img: brightness(zoom_in(img, 0.85), 1.2)],
    # 13 — zoom + flip
    [lambda img: flip_horizontal(zoom_in(img, 0.80))],
    # 14 — contrast tinggi
    [lambda img: contrast(img, 1.5)],
    # 15 — contrast rendah
    [lambda img: contrast(img, 0.6)],
    # 16 — saturasi tinggi
    [lambda img: saturation(img, 1.6)],
    # 17 — saturasi rendah
    [lambda img: saturation(img, 0.5)],
    # 18 — blur ringan
    [lambda img: blur_img(img, 1.0)],
    # 19 — blur + flip
    [lambda img: flip_horizontal(blur_img(img, 1.2))],
    # 20 — sharpen
    [lambda img: sharpness(img, 2.5)],
    # 21 — sharpen + flip
    [lambda img: flip_horizontal(sharpness(img, 2.0))],
    # 22 — noise ringan
    [lambda img: noise(img, 15)],
    # 23 — noise + terang
    [lambda img: brightness(noise(img, 12), 1.1)],
    # 24 — translate kiri
    [lambda img: translate(img, -20, 0)],
    # 25 — translate kanan
    [lambda img: translate(img, 20, 0)],
    # 26 — translate + rotasi
    [lambda img: rotate(translate(img, 15, 10), 8)],
    # 27 — flip + contrast + zoom
    [lambda img: zoom_in(contrast(flip_horizontal(img), 1.3), 0.88)],
    # 28 — rotasi + saturasi
    [lambda img: saturation(rotate(img, -12), 1.4)],
    # 29 — gelap + blur
    [lambda img: blur_img(brightness(img, 0.75), 0.8)],
    # 30 — terang + sharpen + flip
    [lambda img: flip_horizontal(sharpness(brightness(img, 1.25), 1.8))],
]

assert len(RECIPES) == AUG_PER_IMAGE, \
    f"Jumlah resep ({len(RECIPES)}) harus sama dengan AUG_PER_IMAGE ({AUG_PER_IMAGE})"


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

    # Hanya ambil gambar ASLI (bukan aug_)
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
    print("  AUGMENTASI DATASET — 30 variasi per gambar asli")
    print("=" * 55)

    for cls, splits in TARGET.items():
        print(f"\n Kelas: {cls.upper()}")
        for split in splits:
            augment_folder(cls, split)

    cek_distribusi()