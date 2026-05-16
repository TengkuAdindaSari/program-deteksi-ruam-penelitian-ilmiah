"""
model_fusion.py
===============
Arsitektur Multi-Modal Deep Learning:
  - CNN  : ekstrak fitur visual dari citra ruam kulit (MobileNetV2)
  - MLP  : ekstrak fitur klinis dari data gejala
  - Fusion: gabungkan kedua fitur → klasifikasi 3 kelas

Kelas: campak, rubella, cacar

Letakkan di: src\model_fusion.py
"""

import tensorflow as tf
from tensorflow.keras import layers, models, Input
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────

IMG_SHAPE      = (224, 224, 3)   # input citra
NUM_SYMPTOMS   = 6               # jumlah fitur gejala klinis
NUM_CLASSES    = 3               # campak, rubella, cacar
LEARNING_RATE  = 0.0001


# ─────────────────────────────────────────────
# CABANG 1: CNN (Citra)
# Menggunakan MobileNetV2 pretrained ImageNet
# Cocok untuk dataset kecil karena transfer learning
# ─────────────────────────────────────────────

def build_cnn_branch(input_tensor):
    """
    Cabang CNN menggunakan MobileNetV2 sebagai backbone.
    Layer atas di-freeze dulu, fine-tune nanti saat training.

    Return: tensor fitur visual (None, 128)
    """
    backbone = MobileNetV2(
        input_shape = IMG_SHAPE,
        include_top = False,        # hapus fully connected layer asli
        weights     = 'imagenet',   # pakai bobot pretrained
    )

    # Freeze semua layer backbone dulu
    backbone.trainable = False

    x = backbone(input_tensor, training=False)
    x = layers.GlobalAveragePooling2D()(x)   # (None, 1280) → (None, 1280)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    return x   # output: (None, 128)


# ─────────────────────────────────────────────
# CABANG 2: MLP (Gejala Klinis)
# ─────────────────────────────────────────────

def build_mlp_branch(input_tensor):
    """
    Cabang MLP untuk memproses fitur gejala klinis.

    Input : (None, 6) — 6 fitur gejala
    Return: tensor fitur klinis (None, 32)
    """
    x = layers.Dense(64, activation='relu')(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(32, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    return x   # output: (None, 32)


# ─────────────────────────────────────────────
# FUSION: Gabungkan CNN + MLP
# ─────────────────────────────────────────────

def build_fusion_model():
    """
    Membangun model multi-modal lengkap.

    Arsitektur:
        Input Citra (224,224,3) → CNN Branch → fitur visual (128)
                                                        ↓
                                              Concatenate (160)  → Dense → Output (3)
                                                        ↑
        Input Gejala (6,)      → MLP Branch → fitur klinis (32)

    Return:
        model : tf.keras.Model siap di-compile dan di-train
    """

    # ── Input ──
    img_input = Input(shape=IMG_SHAPE,    name='input_citra')
    sym_input = Input(shape=(NUM_SYMPTOMS,), name='input_gejala')

    # ── Cabang ──
    cnn_features = build_cnn_branch(img_input)   # (None, 128)
    mlp_features = build_mlp_branch(sym_input)   # (None, 32)

    # ── Fusion ──
    fused = layers.Concatenate(name='fusion')([cnn_features, mlp_features])  # (None, 160)

    # ── Fully Connected ──
    x = layers.Dense(128, activation='relu', name='fc1')(fused)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(64, activation='relu', name='fc2')(x)
    x = layers.Dropout(0.3)(x)

    # ── Output ──
    output = layers.Dense(NUM_CLASSES, activation='softmax', name='output')(x)

    # ── Build Model ──
    model = models.Model(
        inputs  = [img_input, sym_input],
        outputs = output,
        name    = 'MultiModal_SkinRash'
    )

    return model


# ─────────────────────────────────────────────
# COMPILE MODEL
# ─────────────────────────────────────────────

def compile_model(model):
    """
    Compile model dengan optimizer Adam dan loss categorical crossentropy.

    Return: model yang sudah di-compile
    """
    model.compile(
        optimizer = Adam(learning_rate=LEARNING_RATE),
        loss      = 'sparse_categorical_crossentropy',
        metrics   = ['accuracy']
    )
    return model


# ─────────────────────────────────────────────
# FINE-TUNING (dipakai setelah training awal)
# ─────────────────────────────────────────────

def unfreeze_for_finetuning(model, num_layers_to_unfreeze=30):
    """
    Buka beberapa layer terakhir backbone CNN untuk fine-tuning.
    Dipanggil setelah training awal selesai.

    Parameter:
        model                  : model yang sudah ditraining
        num_layers_to_unfreeze : jumlah layer terakhir yang dibuka (default 30)

    Return: model siap fine-tuning dengan learning rate lebih kecil
    """
    # Cari backbone MobileNetV2 di dalam model
    backbone = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and 'mobilenetv2' in layer.name:
            backbone = layer
            break

    if backbone is None:
        print("[WARNING] Backbone tidak ditemukan.")
        return model

    # Freeze semua layer backbone dulu
    backbone.trainable = True
    for layer in backbone.layers[:-num_layers_to_unfreeze]:
        layer.trainable = False

    trainable_count = sum(1 for l in backbone.layers if l.trainable)
    print(f"Fine-tuning: {trainable_count} layer backbone dibuka")

    # Re-compile dengan learning rate lebih kecil
    model.compile(
        optimizer = Adam(learning_rate=LEARNING_RATE / 10),
        loss      = 'sparse_categorical_crossentropy',
        metrics   = ['accuracy']
    )
    return model


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == '__main__':
    import numpy as np

    print("Membangun model...")
    model = build_fusion_model()
    model = compile_model(model)

    # Tampilkan ringkasan arsitektur
    model.summary()

    # Test forward pass dengan data dummy
    print("\nTest forward pass...")
    dummy_img = np.random.rand(2, 224, 224, 3).astype('float32')
    dummy_sym = np.random.rand(2, 6).astype('float32')
    pred = model.predict([dummy_img, dummy_sym], verbose=0)

    print(f"Input citra : {dummy_img.shape}")
    print(f"Input gejala: {dummy_sym.shape}")
    print(f"Output      : {pred.shape}")
    print(f"Prediksi    : {pred}")
    print("\nModel berhasil dibangun!")