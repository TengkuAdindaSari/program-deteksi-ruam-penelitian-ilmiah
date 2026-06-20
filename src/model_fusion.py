"""
model_fusion.py
===============
Arsitektur Multi-Modal Deep Learning (MobileNetV2 + MLP Fusion):
  - CNN Branch  : Ekstraksi fitur visual dari citra ruam kulit
                  menggunakan MobileNetV2 pre-trained ImageNet
  - MLP Branch  : Ekstraksi fitur klinis dari 13 gejala (symptoms.csv)
  - Fusion Head : Gabungkan kedua fitur -> klasifikasi 3 kelas

Kelas: campak=0, rubella=1, cacar=2

Letakkan di: src/model_fusion.py
"""

import tensorflow as tf
from tensorflow.keras import layers, models, Input, regularizers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam


# =============================================================================
# KONFIGURASI ARSITEKTUR
# =============================================================================
IMG_SHAPE    = (224, 224, 3)
NUM_SYMPTOMS = 13          # Jumlah fitur gejala klinis (lihat symptoms.csv)
NUM_CLASSES  = 3           # campak, rubella, cacar

LR_PHASE1    = 1e-4        # Learning rate Phase 1 (backbone frozen)
LR_PHASE2    = 1e-5        # Learning rate Phase 2 (fine-tuning)
L2_REG       = 1e-4        # L2 regularization weight


# =============================================================================
# CABANG 1: CNN — MobileNetV2 Transfer Learning
# =============================================================================
def build_cnn_branch(input_tensor, trainable_backbone: bool = False):
    """
    Cabang CNN menggunakan MobileNetV2 yang sudah dilatih dengan ImageNet.
    Pada Phase 1: backbone di-freeze (trainable=False).
    Pada Phase 2: beberapa layer terakhir dibuka untuk fine-tuning.
    """
    backbone = MobileNetV2(
        input_shape = IMG_SHAPE,
        include_top = False,
        weights     = 'imagenet',
    )
    backbone.trainable = trainable_backbone

    # Preprocess sesuai standar MobileNetV2 ([-1, 1])
    x = layers.Rescaling(scale=2.0, offset=-1.0, name='mobilenet_preprocess')(input_tensor)
    x = backbone(x, training=trainable_backbone)

    # Classification head untuk cabang CNN
    x = layers.GlobalAveragePooling2D(name='cnn_gap')(x)
    x = layers.Dense(
        256, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='cnn_dense1'
    )(x)
    x = layers.BatchNormalization(name='cnn_bn1')(x)
    x = layers.Dropout(0.4, name='cnn_drop1')(x)
    x = layers.Dense(
        128, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='cnn_dense2'
    )(x)
    x = layers.Dropout(0.3, name='cnn_drop2')(x)
    return x, backbone   # Output: (None, 128), backbone (untuk fine-tuning nanti)


# =============================================================================
# CABANG 2: MLP — 13 Fitur Gejala Klinis
# =============================================================================
def build_mlp_branch(input_tensor):
    """
    Cabang MLP untuk 13 fitur gejala klinis numerik/biner.
    """
    x = layers.Dense(
        64, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='mlp_dense1'
    )(input_tensor)
    x = layers.BatchNormalization(name='mlp_bn1')(x)
    x = layers.Dropout(0.3, name='mlp_drop1')(x)
    x = layers.Dense(
        32, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='mlp_dense2'
    )(x)
    x = layers.Dropout(0.2, name='mlp_drop2')(x)
    return x   # Output: (None, 32)


# =============================================================================
# FUSION MODEL — Gabungkan CNN + MLP
# =============================================================================
def build_fusion_model() -> models.Model:
    """
    Membangun arsitektur full fusion model.

    Arsitektur:
        Input Citra (224,224,3)  ->  MobileNetV2 + Head  ->  (None, 128)  -+
                                                                             |-> Concat(160) -> Dense -> Output(3)
        Input Gejala (13,)       ->  MLP                 ->  (None, 32)   -+
    """
    img_input = Input(shape=IMG_SHAPE,       name='input_citra')
    sym_input = Input(shape=(NUM_SYMPTOMS,), name='input_gejala')

    cnn_out, _ = build_cnn_branch(img_input, trainable_backbone=False)
    mlp_out     = build_mlp_branch(sym_input)

    # Fusion
    fused = layers.Concatenate(name='fusion')([cnn_out, mlp_out])   # (None, 160)

    x = layers.Dense(
        128, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='fc_fusion1'
    )(fused)
    x = layers.BatchNormalization(name='fc_bn1')(x)
    x = layers.Dropout(0.4, name='fc_drop1')(x)
    x = layers.Dense(
        64, activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='fc_fusion2'
    )(x)
    x = layers.Dropout(0.3, name='fc_drop2')(x)

    output = layers.Dense(NUM_CLASSES, activation='softmax', name='output')(x)

    model = models.Model(
        inputs  = [img_input, sym_input],
        outputs = output,
        name    = 'FusionNet_MobileNetV2_MLP'
    )
    return model


def compile_model(model: models.Model, lr: float = LR_PHASE1) -> models.Model:
    """Compile model dengan Adam optimizer dan sparse categorical crossentropy."""
    model.compile(
        optimizer = Adam(learning_rate=lr),
        loss      = 'sparse_categorical_crossentropy',
        metrics   = ['accuracy']
    )
    return model


def unfreeze_for_finetuning(model: models.Model, num_layers_to_unfreeze: int = 30) -> models.Model:
    """
    Buka 'num_layers_to_unfreeze' layer TERAKHIR backbone MobileNetV2
    untuk fine-tuning Phase 2 dengan learning rate lebih kecil.
    """
    backbone = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) and 'mobilenetv2' in layer.name.lower():
            backbone = layer
            break

    if backbone is None:
        print("[WARNING] Backbone MobileNetV2 tidak ditemukan di dalam model!")
        return model

    # Buka backbone sepenuhnya dulu
    backbone.trainable = True

    # Freeze semua kecuali N layer terakhir
    n_total = len(backbone.layers)
    for layer in backbone.layers[:n_total - num_layers_to_unfreeze]:
        layer.trainable = False

    trainable_count   = sum(1 for l in backbone.layers if l.trainable)
    total_backbone    = len(backbone.layers)
    total_trainable   = sum(1 for l in model.layers if l.trainable)

    print(f"  [Fine-Tune] MobileNetV2: {trainable_count}/{total_backbone} layer backbone dibuka")
    print(f"  [Fine-Tune] Total trainable params (model): {model.count_params():,}")

    # Re-compile dengan LR lebih kecil
    model.compile(
        optimizer = Adam(learning_rate=LR_PHASE2),
        loss      = 'sparse_categorical_crossentropy',
        metrics   = ['accuracy']
    )
    return model


# =============================================================================
# QUICK TEST — jalankan: python src/model_fusion.py
# =============================================================================
if __name__ == '__main__':
    import numpy as np

    print("Membangun model FusionNet (MobileNetV2 + MLP)...")
    model = build_fusion_model()
    model = compile_model(model)
    model.summary()

    print("\nTest forward pass dengan data dummy...")
    dummy_img = np.random.rand(2, 224, 224, 3).astype('float32')
    dummy_sym = np.random.rand(2, NUM_SYMPTOMS).astype('float32')
    pred = model.predict({'input_citra': dummy_img, 'input_gejala': dummy_sym}, verbose=0)

    print(f"Input citra : {dummy_img.shape}")
    print(f"Input gejala: {dummy_sym.shape}")
    print(f"Output probs: {pred.shape}")
    print(f"Prediksi    : {pred}")
    print("\nModel berhasil dibangun!")
