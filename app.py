"""
app.py
======
Aplikasi web klasifikasi penyakit ruam kulit menggunakan Streamlit.
Menggunakan model Multi-Modal (CNN + MLP) yang sudah ditraining.

Cara menjalankan (dari root folder):
    (venv) D:\program pi> streamlit run app.py

Pastikan model sudah ditraining dan tersimpan di:
    model\best_model.keras
"""

import os
import numpy as np
import streamlit as st
from PIL import Image
import tensorflow as tf


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────

ROOT_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(ROOT_DIR, 'model', 'best_model.keras')
IMG_SIZE   = (224, 224)
CLASSES    = ['Campak', 'Rubella', 'Cacar Air']

# Info penyakit untuk ditampilkan setelah prediksi
DISEASE_INFO = {
    'Campak': {
        'icon'    : '🔴',
        'deskripsi': 'Campak (Measles) adalah infeksi virus yang sangat menular. '
                     'Ditandai ruam merah yang menyebar dari wajah ke seluruh tubuh.',
        'gejala'  : ['Demam tinggi (38-40°C)', 'Batuk kering', 'Mata merah (konjungtivitis)',
                     'Ruam merah menyebar dari wajah ke badan', 'Bercak Koplik di mulut'],
        'penanganan': 'Istirahat, cukup cairan, konsultasi dokter. Vaksin MMR untuk pencegahan.',
        'warna'   : '#FF4B4B',
    },
    'Rubella': {
        'icon'    : '🟠',
        'deskripsi': 'Rubella (Campak Jerman) adalah infeksi virus yang lebih ringan dari campak. '
                     'Sangat berbahaya jika terjadi pada ibu hamil.',
        'gejala'  : ['Demam ringan (2-3 hari)', 'Ruam merah muda menyebar cepat',
                     'Pembengkakan kelenjar getah bening (belakang telinga/leher)',
                     'Nyeri sendi (pada orang dewasa)'],
        'penanganan': 'Istirahat dan cukup cairan. Vaksin MMR untuk pencegahan. '
                      'Ibu hamil harus segera ke dokter.',
        'warna'   : '#FF8C00',
    },
    'Cacar Air': {
        'icon'    : '🟡',
        'deskripsi': 'Cacar Air (Chickenpox) disebabkan virus Varicella-Zoster. '
                     'Ditandai ruam berupa gelembung kecil berisi cairan yang terasa gatal.',
        'gejala'  : ['Demam ringan-sedang', 'Ruam berupa vesikel (gelembung berisi cairan)',
                     'Sangat gatal', 'Ruam muncul bertahap (kepala → badan → tangan/kaki)',
                     'Vesikel pecah dan mengering membentuk keropeng'],
        'penanganan': 'Jaga kebersihan, jangan digaruk. Obat anti-gatal sesuai anjuran dokter. '
                      'Vaksin Varisela untuk pencegahan.',
        'warna'   : '#FFD700',
    },
}


# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────

@st.cache_resource
def load_model():
    """Load model sekali saja, cache agar tidak reload terus."""
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        return model
    except Exception as e:
        st.error(f"Gagal load model: {e}")
        return None


# ─────────────────────────────────────────────
# PREPROCESSING INPUT
# ─────────────────────────────────────────────

def preprocess_image(uploaded_file):
    """Baca dan preprocess gambar dari upload."""
    img = Image.open(uploaded_file).convert('RGB')
    img_resized = img.resize(IMG_SIZE)
    img_array = np.array(img_resized, dtype=np.float32) / 255.0
    return img, np.expand_dims(img_array, axis=0)   # (1, 224, 224, 3)


def preprocess_symptoms(durasi, batuk, mata_merah, kelenjar, pola_ruam, vesikel):
    """Susun fitur gejala menjadi array numpy."""
    # Normalisasi durasi_demam (StandardScaler sederhana: mean~4, std~1.2)
    durasi_norm = (durasi - 4.0) / 1.2
    features = np.array([[durasi_norm, int(batuk), int(mata_merah),
                          int(kelenjar), int(pola_ruam), int(vesikel)]],
                        dtype=np.float32)
    return features   # (1, 6)


# ─────────────────────────────────────────────
# TAMPILAN HASIL PREDIKSI
# ─────────────────────────────────────────────

def show_result(predicted_class, confidence, all_probs):
    """Tampilkan hasil prediksi dengan styling."""
    info   = DISEASE_INFO[predicted_class]
    warna  = info['warna']

    st.markdown("---")
    st.markdown(f"## {info['icon']} Hasil Prediksi")

    # Kotak hasil utama
    st.markdown(
        f"""
        <div style="background-color:{warna}22; border-left: 5px solid {warna};
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color:{warna}; margin:0;">{predicted_class}</h2>
            <p style="font-size:18px; margin:5px 0;">
                Tingkat keyakinan: <strong>{confidence:.1f}%</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Probabilitas semua kelas
    st.markdown("#### Probabilitas per Kelas")
    for cls, prob in zip(CLASSES, all_probs[0]):
        pct = prob * 100
        st.markdown(f"**{cls}**")
        st.progress(float(prob), text=f"{pct:.1f}%")

    st.markdown("---")

    # Informasi penyakit
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Deskripsi")
        st.info(info['deskripsi'])

        st.markdown("#### 🩺 Gejala Umum")
        for g in info['gejala']:
            st.markdown(f"- {g}")

    with col2:
        st.markdown("#### 💊 Penanganan")
        st.success(info['penanganan'])

        st.markdown("#### ⚠️ Disclaimer")
        st.warning(
            "Hasil ini hanya sebagai referensi awal. "
            "Selalu konsultasikan dengan dokter atau tenaga medis "
            "untuk diagnosis dan penanganan yang tepat."
        )


# ─────────────────────────────────────────────
# HALAMAN UTAMA
# ─────────────────────────────────────────────

def main():
    # Konfigurasi halaman
    st.set_page_config(
        page_title = "Klasifikasi Ruam Kulit",
        page_icon  = "🔬",
        layout     = "wide",
    )

    # Header
    st.title("🔬 Sistem Klasifikasi Penyakit Ruam Kulit")
    st.markdown(
        "Klasifikasi otomatis **Campak**, **Rubella**, dan **Cacar Air** "
        "menggunakan Multi-Modal Deep Learning (CNN + MLP)."
    )
    st.markdown("---")

    # Load model
    model = load_model()

    if model is None:
        st.error(
            "⚠️ Model belum tersedia.\n\n"
            "Jalankan training terlebih dahulu:\n"
            "```\npython src/train.py\n```\n\n"
            "Setelah selesai, model akan tersimpan di folder `model/`."
        )
        st.stop()

    # Layout dua kolom
    col_kiri, col_kanan = st.columns([1, 1], gap="large")

    # ── Kolom Kiri: Input ──
    with col_kiri:
        st.markdown("### 📸 Upload Foto Ruam Kulit")
        uploaded = st.file_uploader(
            "Pilih foto ruam kulit (.jpg / .png)",
            type=["jpg", "jpeg", "png"],
            help="Upload foto ruam kulit yang ingin diklasifikasikan"
        )

        if uploaded:
            img_orig, _ = preprocess_image(uploaded)
            st.image(img_orig, caption="Foto yang diupload", use_column_width=True)

        st.markdown("---")
        st.markdown("### 🩺 Data Gejala Klinis")
        st.caption("Isi gejala yang dialami pasien untuk meningkatkan akurasi prediksi.")

        durasi   = st.slider("Durasi demam (hari)", min_value=0, max_value=14, value=4,
                             help="Berapa hari pasien mengalami demam?")
        batuk    = st.checkbox("Batuk",
                               help="Apakah pasien mengalami batuk?")
        mata     = st.checkbox("Mata merah (konjungtivitis)",
                               help="Apakah mata pasien merah/berair?")
        kelenjar = st.checkbox("Pembengkakan kelenjar getah bening",
                               help="Ada pembengkakan di belakang telinga atau leher?")
        pola     = st.checkbox("Ruam menyebar dari wajah ke badan",
                               help="Apakah ruam mulai dari wajah lalu menyebar ke badan?")
        vesikel  = st.checkbox("Ruam berupa gelembung berisi cairan (vesikel)",
                               help="Apakah ruam berbentuk gelembung kecil berisi cairan?")

        st.markdown("")
        prediksi_btn = st.button("🔍 Prediksi Sekarang",
                                 type="primary",
                                 use_container_width=True,
                                 disabled=(uploaded is None))

        if uploaded is None:
            st.caption("⬆️ Upload foto terlebih dahulu untuk mengaktifkan tombol prediksi.")

    # ── Kolom Kanan: Hasil ──
    with col_kanan:
        st.markdown("### 📊 Hasil Analisis")

        if prediksi_btn and uploaded:
            with st.spinner("Menganalisis gambar dan gejala..."):
                # Preprocessing
                _, img_array = preprocess_image(uploaded)
                sym_array    = preprocess_symptoms(durasi, batuk, mata,
                                                   kelenjar, pola, vesikel)

                # Prediksi
                probs          = model.predict(
                    {'input_citra': img_array, 'input_gejala': sym_array},
                    verbose=0
                )
                pred_idx       = int(np.argmax(probs))
                pred_class     = CLASSES[pred_idx]
                confidence     = float(probs[0][pred_idx]) * 100

            # Tampilkan hasil
            show_result(pred_class, confidence, probs)

        else:
            st.info(
                "Hasil prediksi akan muncul di sini setelah Anda:\n"
                "1. Upload foto ruam kulit\n"
                "2. Isi data gejala klinis\n"
                "3. Klik tombol **Prediksi Sekarang**"
            )

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:13px;'>"
        "Sistem Klasifikasi Penyakit Ruam Kulit | Tugas Akhir | "
        "Multi-Modal Deep Learning (CNN + MLP)"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()