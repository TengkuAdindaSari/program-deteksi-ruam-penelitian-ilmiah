"""
app.py
======
Aplikasi web klasifikasi penyakit ruam kulit menggunakan Streamlit.
Fitur:
  - Dashboard visualisasi dataset & hasil training
  - Prediksi penyakit dari foto + gejala klinis

Cara menjalankan (dari root folder):
    (venv) D:\program pi> streamlit run app.py
"""

import os
import sys
import numpy as np
import streamlit as st
from PIL import Image
import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(ROOT_DIR, 'model', 'best_model.keras')
MODEL_DIR   = os.path.join(ROOT_DIR, 'model')
DATA_DIR    = os.path.join(ROOT_DIR, 'data', 'images')
REPORT_PATH = os.path.join(ROOT_DIR, 'model', 'evaluation_report.txt')
IMG_SIZE    = (224, 224)

CLASSES      = ['campak', 'rubella', 'cacar']
CLASSES_DISP = ['Campak', 'Rubella', 'Cacar Air']

DISEASE_INFO = {
    'Campak': {
        'icon'      : '🔴',
        'deskripsi' : 'Campak (Measles) adalah infeksi virus yang sangat menular. '
                      'Ditandai ruam merah yang menyebar dari wajah ke seluruh tubuh.',
        'gejala'    : ['Demam tinggi (38-40°C)', 'Batuk kering',
                       'Mata merah (konjungtivitis)',
                       'Ruam merah menyebar dari wajah ke badan',
                       'Bercak Koplik di mulut'],
        'penanganan': 'Istirahat, cukup cairan, konsultasi dokter. Vaksin MMR untuk pencegahan.',
        'warna'     : '#FF4B4B',
    },
    'Rubella': {
        'icon'      : '🟠',
        'deskripsi' : 'Rubella (Campak Jerman) adalah infeksi virus yang lebih ringan dari campak. '
                      'Sangat berbahaya jika terjadi pada ibu hamil.',
        'gejala'    : ['Demam ringan (2-3 hari)', 'Ruam merah muda menyebar cepat',
                       'Pembengkakan kelenjar getah bening (belakang telinga/leher)',
                       'Nyeri sendi (pada orang dewasa)'],
        'penanganan': 'Istirahat dan cukup cairan. Vaksin MMR untuk pencegahan. '
                      'Ibu hamil harus segera ke dokter.',
        'warna'     : '#FF8C00',
    },
    'Cacar Air': {
        'icon'      : '🟡',
        'deskripsi' : 'Cacar Air (Chickenpox) disebabkan virus Varicella-Zoster. '
                      'Ditandai ruam berupa gelembung kecil berisi cairan yang terasa gatal.',
        'gejala'    : ['Demam ringan-sedang', 'Ruam berupa vesikel (gelembung berisi cairan)',
                       'Sangat gatal',
                       'Ruam muncul bertahap (kepala → badan → tangan/kaki)',
                       'Vesikel pecah dan mengering membentuk keropeng'],
        'penanganan': 'Jaga kebersihan, jangan digaruk. Obat anti-gatal sesuai anjuran dokter. '
                      'Vaksin Varisela untuk pencegahan.',
        'warna'     : '#FFD700',
    },
}


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return tf.keras.models.load_model(MODEL_PATH)
    except Exception as e:
        st.error(f"Gagal load model: {e}")
        return None


def count_images():
    """Hitung jumlah gambar per kelas per split."""
    result = {}
    splits = ['training', 'validasi', 'test']
    for cls in CLASSES:
        result[cls] = {}
        for split in splits:
            folder = os.path.join(DATA_DIR, cls, split)
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder)
                         if os.path.splitext(f)[1].lower()
                         in {'.jpg', '.jpeg', '.png', '.bmp'}]
                asli = len([f for f in files if not f.startswith('aug_')])
                aug  = len([f for f in files if f.startswith('aug_')])
                result[cls][split] = {'total': len(files), 'asli': asli, 'aug': aug}
            else:
                result[cls][split] = {'total': 0, 'asli': 0, 'aug': 0}
    return result


def preprocess_image(uploaded_file):
    img = Image.open(uploaded_file).convert('RGB')
    img_resized = img.resize(IMG_SIZE)
    img_array = np.array(img_resized, dtype=np.float32) / 255.0
    return img, np.expand_dims(img_array, axis=0)


def preprocess_symptoms(durasi, batuk, mata_merah, kelenjar, pola_ruam, vesikel):
    durasi_norm = (durasi - 4.0) / 1.2
    features = np.array([[durasi_norm, int(batuk), int(mata_merah),
                          int(kelenjar), int(pola_ruam), int(vesikel)]],
                        dtype=np.float32)
    return features


# ─────────────────────────────────────────────
# HALAMAN: DASHBOARD
# ─────────────────────────────────────────────

def page_dashboard():
    st.markdown("## 📊 Dashboard Visualisasi")
    st.markdown("Ringkasan dataset dan hasil training model.")

    # ── Statistik Dataset ──
    st.markdown("### 🗂️ Distribusi Dataset")
    img_counts = count_images()

    splits = ['training', 'validasi', 'test']
    split_labels = ['Training', 'Validasi', 'Test']

    # Tabel distribusi
    rows = []
    for cls in CLASSES:
        row = {'Kelas': cls.capitalize()}
        for split in splits:
            row[split.capitalize()] = img_counts[cls][split]['total']
        row['Total'] = sum(img_counts[cls][s]['total'] for s in splits)
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Bar chart distribusi training
    st.markdown("#### Distribusi Training Data")
    fig, ax = plt.subplots(figsize=(8, 4))
    kelas_names = [c.capitalize() for c in CLASSES]
    train_counts = [img_counts[c]['training']['total'] for c in CLASSES]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = ax.bar(kelas_names, train_counts, color=colors, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, train_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                str(val), ha='center', va='bottom', fontweight='bold', fontsize=12)
    ax.set_ylabel('Jumlah Gambar', fontsize=11)
    ax.set_title('Distribusi Kelas Training Data', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(train_counts) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    st.pyplot(fig)
    plt.close()

    # Asli vs Augmentasi
    st.markdown("#### Asli vs Augmentasi (Training)")
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    x = np.arange(len(CLASSES))
    w = 0.35
    asli_counts = [img_counts[c]['training']['asli'] for c in CLASSES]
    aug_counts  = [img_counts[c]['training']['aug']  for c in CLASSES]
    ax2.bar(x - w/2, asli_counts, w, label='Asli',       color='#FF6B6B', edgecolor='white')
    ax2.bar(x + w/2, aug_counts,  w, label='Augmentasi', color='#4ECDC4', edgecolor='white')
    ax2.set_xticks(x)
    ax2.set_xticklabels(kelas_names)
    ax2.set_ylabel('Jumlah Gambar')
    ax2.set_title('Gambar Asli vs Augmentasi', fontweight='bold')
    ax2.legend()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    st.pyplot(fig2)
    plt.close()

    st.markdown("---")

    # ── Hasil Training ──
    st.markdown("### 📈 Hasil Training")

    # Grafik history phase 1
    p1_path = os.path.join(MODEL_DIR, 'history_phase1_frozen.png')
    p2_path = os.path.join(MODEL_DIR, 'history_phase2_finetune.png')
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')

    if os.path.exists(p1_path) and os.path.exists(p2_path):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Phase 1 — Backbone Frozen**")
            st.image(p1_path, use_column_width=True)
        with col2:
            st.markdown("**Phase 2 — Fine-tuning**")
            st.image(p2_path, use_column_width=True)
    else:
        st.info("Grafik training belum tersedia. Jalankan training terlebih dahulu.")

    # Confusion Matrix
    if os.path.exists(cm_path):
        st.markdown("### 🔢 Confusion Matrix")
        st.image(cm_path, use_column_width=True)

    # Evaluation Report
    if os.path.exists(REPORT_PATH):
        st.markdown("### 📋 Laporan Evaluasi")
        with open(REPORT_PATH, 'r') as f:
            report = f.read()
        st.code(report, language='text')
    else:
        st.info("Laporan evaluasi belum tersedia. Jalankan training terlebih dahulu.")


# ─────────────────────────────────────────────
# HALAMAN: PREDIKSI
# ─────────────────────────────────────────────

def page_prediksi():
    st.markdown("## 🔍 Prediksi Penyakit Ruam Kulit")

    model = load_model()
    if model is None:
        st.error(
            "⚠️ Model belum tersedia.\n\n"
            "Jalankan training terlebih dahulu:\n"
            "```\npython src/train.py\n```"
        )
        return

    col_kiri, col_kanan = st.columns([1, 1], gap="large")

    with col_kiri:
        st.markdown("### 📸 Upload Foto Ruam Kulit")
        uploaded = st.file_uploader(
            "Pilih foto ruam kulit (.jpg / .png)",
            type=["jpg", "jpeg", "png"]
        )
        if uploaded:
            img_orig, _ = preprocess_image(uploaded)
            st.image(img_orig, caption="Foto yang diupload", use_column_width=True)

        st.markdown("---")
        st.markdown("### 🩺 Data Gejala Klinis")
        st.caption("Isi gejala yang dialami untuk meningkatkan akurasi prediksi.")

        durasi   = st.slider("Durasi demam (hari)", 0, 14, 4)
        batuk    = st.checkbox("Batuk")
        mata     = st.checkbox("Mata merah (konjungtivitis)")
        kelenjar = st.checkbox("Pembengkakan kelenjar getah bening")
        pola     = st.checkbox("Ruam menyebar dari wajah ke badan")
        vesikel  = st.checkbox("Ruam berupa gelembung berisi cairan (vesikel)")

        st.markdown("")
        prediksi_btn = st.button(
            "🔍 Prediksi Sekarang",
            type="primary",
            use_container_width=True,
            disabled=(uploaded is None)
        )
        if uploaded is None:
            st.caption("⬆️ Upload foto terlebih dahulu.")

    with col_kanan:
        st.markdown("### 📊 Hasil Analisis")

        if prediksi_btn and uploaded:
            with st.spinner("Menganalisis..."):
                _, img_array = preprocess_image(uploaded)
                sym_array    = preprocess_symptoms(durasi, batuk, mata,
                                                   kelenjar, pola, vesikel)
                probs    = model.predict(
                    {'input_citra': img_array, 'input_gejala': sym_array},
                    verbose=0
                )
                pred_idx   = int(np.argmax(probs))
                pred_class = CLASSES_DISP[pred_idx]
                confidence = float(probs[0][pred_idx]) * 100

            # Tampilkan hasil
            info  = DISEASE_INFO[pred_class]
            warna = info['warna']

            st.markdown(
                f"""
                <div style="background:{warna}22; border-left:5px solid {warna};
                            padding:20px; border-radius:10px; margin-bottom:15px;">
                    <h2 style="color:{warna}; margin:0;">{info['icon']} {pred_class}</h2>
                    <p style="font-size:18px; margin:5px 0;">
                        Keyakinan: <strong>{confidence:.1f}%</strong>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Probabilitas semua kelas
            st.markdown("#### Probabilitas per Kelas")
            for cls_disp, prob in zip(CLASSES_DISP, probs[0]):
                st.markdown(f"**{cls_disp}** — {prob*100:.1f}%")
                st.progress(float(prob))

            st.markdown("---")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### 📋 Deskripsi")
                st.info(info['deskripsi'])
                st.markdown("#### 🩺 Gejala Umum")
                for g in info['gejala']:
                    st.markdown(f"- {g}")
            with col_b:
                st.markdown("#### 💊 Penanganan")
                st.success(info['penanganan'])
                st.markdown("#### ⚠️ Disclaimer")
                st.warning(
                    "Hasil ini hanya referensi awal. "
                    "Selalu konsultasikan dengan dokter untuk diagnosis yang tepat."
                )
        else:
            st.info(
                "Hasil prediksi akan muncul di sini setelah:\n"
                "1. Upload foto ruam kulit\n"
                "2. Isi data gejala klinis\n"
                "3. Klik **Prediksi Sekarang**"
            )


# ─────────────────────────────────────────────
# HALAMAN: TENTANG MODEL
# ─────────────────────────────────────────────

def page_tentang():
    st.markdown("## ℹ️ Tentang Model")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Arsitektur", "CNN + MLP")
    with col2:
        st.metric("Backbone CNN", "MobileNetV2")
    with col3:
        st.metric("Jumlah Kelas", "3")

    st.markdown("---")
    st.markdown("### 🏗️ Arsitektur Multi-Modal")
    st.code("""
Input Citra (224×224×3)
        ↓
  MobileNetV2 (pretrained ImageNet)
        ↓
  GlobalAveragePooling → Dense(256) → Dense(128)
        ↓ fitur visual (128)
                            → Concatenate → Dense(128) → Dense(64) → Output(3)
        ↑ fitur klinis (32)
  Dense(64) → Dense(32)
        ↑
Input Gejala Klinis (6 fitur)
    """, language='text')

    st.markdown("### 📌 Fitur Gejala Klinis")
    fitur_df = pd.DataFrame({
        'Fitur'      : ['Durasi Demam', 'Batuk', 'Mata Merah',
                        'Kelenjar Bengkak', 'Pola Ruam', 'Vesikel'],
        'Tipe'       : ['Numerik (hari)', 'Biner', 'Biner',
                        'Biner', 'Biner', 'Biner'],
        'Keterangan' : ['Lama demam dalam hari',
                        'Ada/tidak batuk',
                        'Konjungtivitis',
                        'Kelenjar getah bening bengkak',
                        'Ruam menyebar wajah ke badan',
                        'Ruam berupa gelembung cairan'],
    })
    st.dataframe(fitur_df, use_container_width=True, hide_index=True)

    st.markdown("### 🎯 Performa Model")
    perf_df = pd.DataFrame({
        'Kelas'    : ['Campak', 'Rubella', 'Cacar Air', 'Overall'],
        'Precision': [0.94, 0.50, 0.97, 0.93],
        'Recall'   : [0.89, 0.56, 0.99, 0.93],
        'F1-Score' : [0.91, 0.53, 0.98, 0.93],
        'Support'  : [83, 9, 113, 205],
    })
    st.dataframe(perf_df, use_container_width=True, hide_index=True)

    st.info(
        "**Catatan:** F1-Score rubella yang rendah (0.53) dipengaruhi oleh "
        "keterbatasan data uji yang hanya terdiri dari 9 sampel. "
        "Hal ini menjadi keterbatasan penelitian yang perlu ditingkatkan."
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title = "Deteksi Ruam Kulit",
        page_icon  = "🔬",
        layout     = "wide",
    )

    # Header
    st.title("🔬 Sistem Klasifikasi Penyakit Ruam Kulit")
    st.markdown(
        "**Multimodal Deep Learning: CNN + MLP** | "
        "Klasifikasi Campak, Rubella, dan Cacar Air"
    )
    st.markdown("---")

    # Navigasi
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Prediksi", "ℹ️ Tentang Model"])

    with tab1:
        page_dashboard()
    with tab2:
        page_prediksi()
    with tab3:
        page_tentang()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:12px;'>"
        "Sistem Klasifikasi Penyakit Ruam Kulit | Tugas Akhir | "
        "Multi-Modal Deep Learning (CNN + MLP) | 2025"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()                                                              