"""
model_fusion.py
===============
Arsitektur Multi-Modal Deep Learning:
  - CNN  : ekstrak fitur visual dari citra ruam kulit (MobileNetV2)
  - MLP  : ekstrak fitur klinis dari 13 gejala (lihat symptoms.csv)
  - Fusion: gabungkan kedua fitur -> klasifikasi 3 kelas

Kelas: campak, rubella, cacar

Letakkan di: src/model_fusion.py
"""

import tensorflow as tf
from tensorflow.keras import layers, models, Input
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
IMG_SHAPE     = (224, 224, 3)
NUM_SYMPTOMS  = 10               # jumlah fitur gejala klinis (setelah durasi_demam & pilek dihapus)
NUM_CLASSES   = 3                # campak, rubella, cacar
LEARNING_RATE = 0.0001


# ─────────────────────────────────────────────
# CABANG 1: CNN (Citra) — MobileNetV2 transfer learning
# ─────────────────────────────────────────────

def build_cnn_branch(input_tensor):
    """Cabang CNN. Backbone di-freeze dulu, fine-tune di Phase 2."""
    backbone = MobileNetV2(
        input_shape = IMG_SHAPE,
        include_top = False,
        weights     = 'imagenet',
    )
    backbone.trainable = False

    x = backbone(input_tensor, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    return x   # output: (None, 128)


# ─────────────────────────────────────────────
# CABANG 2: MLP (Gejala Klinis — 13 fitur)
# ─────────────────────────────────────────────

def build_mlp_branch(input_tensor):
    """Cabang MLP untuk 10 fitur gejala klinis."""
    x = layers.Dense(64, activation='relu')(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(32, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    return x   # output: (None, 32)


# ─────────────────────────────────────────────
# FUSION: Gabungkan CNN + MLP
# ─────────────────────────────────────────────

def build_fusion_model() -> models.Model:
    """
    Arsitektur:
        Input Citra (224,224,3) -> CNN Branch -> fitur visual (128)
                                                          |
                                                Concatenate (160) -> Dense -> Output (3)
                                                          |
        Input Gejala (13,)      -> MLP Branch -> fitur klinis (32)
    """
    img_input = Input(shape=IMG_SHAPE,       name='input_citra')
    sym_input = Input(shape=(NUM_SYMPTOMS,), name='input_gejala')

    cnn_features = build_cnn_branch(img_input)   # (None, 128)
    mlp_features = build_mlp_branch(sym_input)   # (None, 32)

    fused = layers.Concatenate(name='fusion')([cnn_features, mlp_features])  # (None, 160)

    x = layers.Dense(128, activation='relu', name='fc1')(fused)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(64, activation='relu', name='fc2')(x)
    x = layers.Dropout(0.4)(x)

    output = layers.Dense(NUM_CLASSES, activation='softmax', name='output')(x)

    model = models.Model(
        inputs  = [img_input, sym_input],
        outputs = output,
        name    = 'MultiModal_SkinRash'
    )
    return model


def compile_model(model: models.Model) -> models.Model:
    model.compile(
        optimizer = Adam(learning_rate=LEARNING_RATE),
        loss      = 'sparse_categorical_crossentropy',
        metrics   = ['accuracy']
    )
    return model


def unfreeze_for_finetuning(model: models.Model, num_layers_to_unfreeze: int = 30) -> models.Model:
    """Buka beberapa layer terakhir backbone CNN untuk fine-tuning."""
    backbone = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and 'mobilenetv2' in layer.name:
            backbone = layer
            break

    if backbone is None:
        print("[WARNING] Backbone tidak ditemukan.")
        return model

    backbone.trainable = True
    for layer in backbone.layers[:-num_layers_to_unfreeze]:
        layer.trainable = False

    trainable_count = sum(1 for l in backbone.layers if l.trainable)
    print(f"Fine-tuning: {trainable_count} layer backbone dibuka")

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
    model.summary()

    print("\nTest forward pass...")
    dummy_img = np.random.rand(2, 224, 224, 3).astype('float32')
    dummy_sym = np.random.rand(2, NUM_SYMPTOMS).astype('float32')
    pred = model.predict([dummy_img, dummy_sym], verbose=0)

    print(f"Input citra : {dummy_img.shape}")
    print(f"Input gejala: {dummy_sym.shape}")
    print(f"Output      : {pred.shape}")
    print(f"Prediksi    : {pred}")
    print("\nModel berhasil dibangun!")
