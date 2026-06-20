"""
streamlit_app.py
================
Aplikasi web klasifikasi penyakit ruam kulit menggunakan Streamlit.
Didesain secara modern dan premium dengan visualisasi yang interaktif.

Fitur:
  - Dashboard visualisasi dataset & hasil training (dinamis)
  - Prediksi penyakit dari foto ruam kulit + 13 gejala klinis
  - Detail arsitektur model Fusion (CNN MobileNetV2 + MLP)

Cara menjalankan:
    (venv) streamlit run src/streamlit_app.py
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import tensorflow as tf

# ─────────────────────────────────────────────
# KONFIGURASI PATH
# ─────────────────────────────────────────────
SRC_DIR      = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.dirname(SRC_DIR)
MODEL_DIR    = os.path.join(ROOT_DIR, 'model')
MODEL_PATH   = os.path.join(MODEL_DIR, 'best_model.keras')
SCALER_PATH  = os.path.join(MODEL_DIR, 'scaler.pkl')
REPORT_PATH  = os.path.join(MODEL_DIR, 'evaluation_report.txt')

CLASSES      = ['campak', 'rubella', 'cacar']
CLASSES_DISP = ['Campak', 'Rubella', 'Cacar Air']
IMG_SIZE     = (224, 224)

# Informasi Penyakit
DISEASE_INFO = {
    'Campak': {
        'icon'      : '🔴',
        'deskripsi' : 'Campak (Measles) adalah infeksi virus yang sangat menular. '
                      'Ditandai ruam merah khas yang menyebar dari wajah ke seluruh tubuh.',
        'gejala'    : ['Demam tinggi (38-40°C)', 'Batuk kering & Pilek',
                       'Mata merah & berair (konjungtivitis)',
                       'Ruam merah menyebar makulopapular',
                       'Bercak Koplik (koplik spot) di mulut'],
        'penanganan': 'Istirahat total, cukup cairan, konsumsi penurun demam, dan suplemen Vitamin A. '
                      'Pencegahan terbaik adalah melalui vaksinasi MMR.',
        'warna'     : '#FF4B4B',
    },
    'Rubella': {
        'icon'      : '🟠',
        'deskripsi' : 'Rubella (Campak Jerman) adalah infeksi virus ringan pada anak, namun '
                      'sakit keras dan berisiko tinggi jika menular pada ibu hamil (menyebabkan kecacatan janin).',
        'gejala'    : ['Demam ringan-sedang', 'Ruam merah muda menyebar cepat (2-3 hari)',
                       'Pembengkakan kelenjar getah bening di belakang telinga/leher',
                       'Nyeri sendi (umum pada pasien dewasa)'],
        'penanganan': 'Terapi suportif berupa istirahat dan hidrasi yang cukup. '
                      'Ibu hamil yang terpapar harus segera menghubungi dokter spesialis.',
        'warna'     : '#FF8C00',
    },
    'Cacar Air': {
        'icon'      : '🟡',
        'deskripsi' : 'Cacar Air (Chickenpox) disebabkan oleh virus Varicella-Zoster. '
                      'Sangat khas dengan ruam berbentuk lenting kemerahan berisi cairan gatal.',
        'gejala'    : ['Demam ringan-sedang', 'Ruam berupa vesikel (gelembung berisi cairan)',
                       'Rasa gatal yang sangat intens',
                       'Vesikel muncul bertahap lalu pecah dan mengering membentuk keropeng'],
        'penanganan': 'Jaga kebersihan kulit, hindari menggaruk vesikel agar tidak infeksi sekunder/membekas, '
                      'gunakan bedak salisilat dingin atau lotion kalamin. Konsultasikan antivirus ke dokter.',
        'warna'     : '#FFD700',
    },
}

# ─────────────────────────────────────────────
# LOAD MODEL & SCALER
# ─────────────────────────────────────────────
@st.cache_resource
def load_classification_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return tf.keras.models.load_model(MODEL_PATH)
    except Exception as e:
        st.error(f"Gagal memuat model keras: {e}")
        return None

@st.cache_resource
def load_scaler():
    if not os.path.exists(SCALER_PATH):
        return None
    try:
        with open(SCALER_PATH, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"Gagal memuat scaler: {e}")
        return None

# ─────────────────────────────────────────────
# HELPER: HITUNG JUMLAH GAMBAR SECARA DINAMIS
# ─────────────────────────────────────────────
def count_images_dynamically():
    result = {}
    splits = ['train', 'test']
    for cls in CLASSES:
        result[cls] = {}
        for split in splits:
            folder = os.path.join(ROOT_DIR, 'data', 'images', cls, split)
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder)
                         if os.path.splitext(f)[1].lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}]
                asli = len([f for f in files if not f.startswith('aug_')])
                aug  = len([f for f in files if f.startswith('aug_')])
                result[cls][split] = {'total': len(files), 'asli': asli, 'aug': aug}
            else:
                result[cls][split] = {'total': 0, 'asli': 0, 'aug': 0}
    return result

# Preprocessing Citra untuk Inferensi
def preprocess_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file).convert('RGB')
    img_resized = img.resize(IMG_SIZE)
    img_array = np.array(img_resized, dtype=np.float32) / 255.0
    return img, np.expand_dims(img_array, axis=0)

# ─────────────────────────────────────────────
# DESAIN PREMIUM CSS CUSTOM
# ─────────────────────────────────────────────
def apply_premium_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    .app-title-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, rgba(255, 75, 75, 0.05), rgba(255, 140, 0, 0.05));
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 75, 75, 0.1);
    }
    .app-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B, #FF8C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    .custom-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #f0f2f6;
        margin-bottom: 1.5rem;
    }
    .dark-card {
        background-color: #1e222b;
        border-radius: 12px;
        padding: 1.5rem;
        color: #e2e8f0;
        border: 1px solid #2d3748;
        margin-bottom: 1.5rem;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FF4B4B;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HALAMAN 1: DASHBOARD
# ─────────────────────────────────────────────
def show_dashboard_page():
    st.markdown("<h2 style='color:#FF4B4B;'>📊 Dashboard Performa & Data</h2>", unsafe_allow_html=True)
    st.markdown("Visualisasi ringkasan dataset terbaru serta grafik riwayat pelatihan model.")

    img_counts = count_images_dynamically()

    splits = ['train', 'test']
    rows = []
    for cls in CLASSES:
        row = {'Kelas': cls.capitalize()}
        for split in splits:
            row[split.capitalize()] = img_counts[cls][split]['total']
        row['Total'] = sum(img_counts[cls][s]['total'] for s in splits)
        rows.append(row)

    df_counts = pd.DataFrame(rows)

    col_table, col_chart = st.columns([1, 1], gap="medium")

    with col_table:
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_counts, use_container_width=True, hide_index=True)
        st.caption("Catatan: Data Train sudah ditambahkan hasil augmentasi citra (+15 gambar per gambar asli).")

        total_train = sum(img_counts[c]['train']['total'] for c in CLASSES)
        total_test = sum(img_counts[c]['test']['total'] for c in CLASSES)
        
        st.markdown(
            f"""
            <div style="display: flex; gap: 15px; margin-top: 15px;">
                <div class="custom-card" style="flex: 1; text-align: center; margin:0;">
                    <div class="metric-label">Total Data Train</div>
                    <div class="metric-value" style="color: #4ECDC4;">{total_train}</div>
                </div>
                <div class="custom-card" style="flex: 1; text-align: center; margin:0;">
                    <div class="metric-label">Total Data Test</div>
                    <div class="metric-value" style="color: #FF8C00;">{total_test}</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with col_chart:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        classes_disp = [c.capitalize() for c in CLASSES]
        train_vals = [img_counts[c]['train']['total'] for c in CLASSES]
        test_vals = [img_counts[c]['test']['total'] for c in CLASSES]
        
        x = np.arange(len(CLASSES))
        width = 0.35
        
        ax.bar(x - width/2, train_vals, width, label='Train (Augmented)', color='#4ECDC4', edgecolor='white')
        ax.bar(x + width/2, test_vals, width, label='Test (Original)', color='#FF8C00', edgecolor='white')
        
        ax.set_ylabel('Jumlah Sampel Citra')
        ax.set_title('Distribusi Data Per Kelas')
        ax.set_xticks(x)
        ax.set_xticklabels(classes_disp)
        ax.legend()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("---")

    st.markdown("### 📈 Grafik Proses & Hasil Pelatihan")

    p1_path = os.path.join(MODEL_DIR, 'history_phase1_frozen.png')
    p2_path = os.path.join(MODEL_DIR, 'history_phase2_finetune.png')
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown("#### Kurva Akurasi & Loss")
        if os.path.exists(p1_path) and os.path.exists(p2_path):
            subtab1, subtab2 = st.tabs(["Phase 1 (Backbone Frozen)", "Phase 2 (Fine-Tuning)"])
            with subtab1:
                st.image(p1_path, use_container_width=True)
            with subtab2:
                st.image(p2_path, use_container_width=True)
        else:
            st.info("Kurva training belum tersedia. Jalankan script training terlebih dahulu.")

    with col2:
        st.markdown("#### Matriks Kebingungan (Confusion Matrix)")
        if os.path.exists(cm_path):
            st.image(cm_path, use_container_width=True)
        else:
            st.info("Confusion matrix belum tersedia. Jalankan training terlebih dahulu.")

    st.markdown("---")

    st.markdown("### 📋 Laporan Evaluasi Terakhir (Test Set)")
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, 'r') as f:
            report_text = f.read()
        st.code(report_text, language='text')
    else:
        st.info("Laporan evaluasi belum tersedia. Jalankan training untuk membuatnya.")

# ─────────────────────────────────────────────
# HALAMAN 2: PREDIKSI
# ─────────────────────────────────────────────
def show_prediction_page():
    st.markdown("<h2 style='color:#FF8C00;'>🔍 Deteksi & Diagnosis Ruam Kulit</h2>", unsafe_allow_html=True)
    st.markdown("Unggah foto ruam kulit pasien dan isi checklist gejala klinis di bawah ini untuk diagnosa.")

    model = load_classification_model()
    scaler = load_scaler()

    if model is None:
        st.error(
            "⚠️ Model Klasifikasi (`best_model.keras`) belum ditemukan di folder `model/`!\n\n"
            "Silakan jalankan proses training terlebih dahulu dengan perintah:\n"
            "```bash\npython src/train.py\n```"
        )
        return

    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("### 1. Unggah Citra Ruam")
        uploaded_file = st.file_uploader("Pilih file foto ruam (.jpg / .jpeg / .png)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Foto berhasil diunggah", use_container_width=True)

        st.markdown("### 2. Checklist Gejala Klinis")
        st.caption("Pilih kondisi gejala yang dirasakan oleh pasien saat ini.")

        durasi_demam = st.slider("Lama / Durasi Demam (Hari)", min_value=0, max_value=14, value=3)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            demam_tinggi = st.checkbox("Mengalami Demam Tinggi (>38.5°C)")
            batuk = st.checkbox("Batuk Kering")
            pilek = st.checkbox("Pilek / Hidung Tersumbat")
            sakit_tenggorokan = st.checkbox("Sakit Tenggorokan")
            konjungtivitis = st.checkbox("Mata Merah & Berair")
            koplik_spot = st.checkbox("Bercak Koplik (Bintik Putih di Mulut)")
        
        with col_g2:
            kelenjar_bengkak = st.checkbox("Pembengkakan Kelenjar (Leher/Telinga)")
            ruam_wajah_ke_leher = st.checkbox("Ruam Awal Muncul di Wajah/Leher")
            nyeri_sendi = st.checkbox("Nyeri Sendi / Pegal-pegal")
            vesikel = st.checkbox("Lenting / Gelembung Berisi Cairan")
            hilang_nafsu_makan = st.checkbox("Hilang Nafsu Makan")
            lemas = st.checkbox("Badan Lemas & Cepat Lelah")

        predict_btn = st.button("Diagnosis Sekarang", type="primary", use_container_width=True)

    with col_result:
        st.markdown("### 3. Hasil Diagnosis")
        
        if predict_btn and uploaded_file:
            with st.spinner("Model sedang memproses citra dan data gejala..."):
                _, img_batch = preprocess_uploaded_image(uploaded_file)
                
                if scaler is not None:
                    durasi_norm = float(scaler.transform([[durasi_demam]])[0][0])
                else:
                    durasi_norm = (durasi_demam - 4.0) / 1.2
                
                symptom_vector = np.array([[
                    durasi_norm,
                    int(demam_tinggi),
                    int(batuk),
                    int(pilek),
                    int(sakit_tenggorokan),
                    int(konjungtivitis),
                    int(koplik_spot),
                    int(kelenjar_bengkak),
                    int(ruam_wajah_ke_leher),
                    int(nyeri_sendi),
                    int(vesikel),
                    int(hilang_nafsu_makan),
                    int(lemas)
                ]], dtype=np.float32)

                preds = model.predict(
                    {'input_citra': img_batch, 'input_gejala': symptom_vector},
                    verbose=0
                )
                
                pred_idx = int(np.argmax(preds[0]))
                pred_class = CLASSES_DISP[pred_idx]
                confidence = float(preds[0][pred_idx]) * 100

                info = DISEASE_INFO[pred_class]
                color = info['warna']

                st.markdown(
                    f"""
                    <div style="background-color: {color}15; border-left: 6px solid {color}; 
                                padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <span style="font-size: 0.9rem; font-weight: 600; text-transform: uppercase; color: {color}dd;">Hasil Klasifikasi Terdeteksi</span>
                        <h2 style="color: {color}; margin: 5px 0 10px 0; font-size: 2.2rem;">{info['icon']} {pred_class}</h2>
                        <p style="font-size: 1.2rem; margin: 0; color: #2d3748;">
                            Tingkat Kepercayaan (Confidence): <strong>{confidence:.2f}%</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True
                )

                st.markdown("#### Skor Keyakinan Semua Kelas:")
                for i, c_disp in enumerate(CLASSES_DISP):
                    score = float(preds[0][i])
                    st.markdown(f"**{c_disp}** ({score*100:.1f}%)")
                    st.progress(score)

                st.markdown("---")

                st.markdown(f"### {info['icon']} Detail Penyakit: {pred_class}")
                st.markdown(f"**Deskripsi:**\n{info['deskripsi']}")
                
                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    st.markdown("**Gejala Umum:**")
                    for g in info['gejala']:
                        st.markdown(f"- {g}")
                with col_det2:
                    st.markdown("**Saran Penanganan:**")
                    st.success(info['penanganan'])

                st.warning(
                    "⚠️ **DISCLAIMER**: Hasil analisis model kecerdasan buatan ini bersifat referensi akademis awal "
                    "dan tidak menggantikan diagnosis klinis resmi dari dokter ahli."
                )
        else:
            st.info(
                "Menunggu input pasien. Silakan:\n"
                "1. Unggah foto ruam kulit di panel kiri\n"
                "2. Isi checklist gejala yang dialami\n"
                "3. Klik tombol **Diagnosis Sekarang**"
            )

# ─────────────────────────────────────────────
# HALAMAN 3: TENTANG MODEL FUSION
# ─────────────────────────────────────────────
def show_about_page():
    st.markdown("<h2 style='color:#4ECDC4;'>ℹ️ Tentang Arsitektur Multi-Modal</h2>", unsafe_allow_html=True)
    st.markdown("Sistem klasifikasi ini dirancang menggunakan konsep **Late Fusion Deep Learning**.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Arsitektur Sistem", "Late Fusion Network")
    with col2:
        st.metric("Backbone CNN (Citra)", "MobileNetV2 (Pre-trained)")
    with col3:
        st.metric("Dimensi Input Gejala", "13 Fitur Klinis")

    st.markdown("---")
    
    st.markdown("### 🧱 Skema Penggabungan Fitur (Fusion)")
    st.code("""
Citra Ruam (224x224x3)  ──► [ MobileNetV2 Backbone ] ──► GAP ──► Dense(256) ──► Dense(128) ──┐
                                                                                           ├─► [ Concatenate ] (160) ──► Dense(128) ──► Dense(64) ──► Softmax (3 Kelas)
Gejala Klinis (13 Dim)   ──► [ Dense(64) ] ──► Batch Normalization ──► Dense(32) ───────────┘
    """, language='text')

    st.markdown("### 📋 Daftar 13 Fitur Gejala Klinis")
    fitur_data = {
        'Nama Fitur': [
            'Durasi Demam', 'Demam Tinggi', 'Batuk', 'Pilek', 'Sakit Tenggorokan',
            'Konjungtivitis', 'Koplik Spot', 'Kelenjar Bengkak', 'Ruam Wajah ke Leher',
            'Nyeri Sendi', 'Vesikel', 'Hilang Nafsu Makan', 'Lemas'
        ],
        'Tipe Data': [
            'Numerik (0-14 Hari)', 'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)',
            'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)',
            'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)', 'Biner (0/1)'
        ],
        'Keterangan Deskriptif': [
            'Lama demam berlangsung sejak awal gejala',
            'Apakah demam tinggi melebihi 38.5 derajat Celcius',
            'Adanya batuk kering yang menyertai',
            'Adanya pilek atau hidung tersumbat',
            'Adanya radang atau sakit saat menelan',
            'Mata berwarna merah dan terasa perih/berair',
            'Bercak putih keabu-abuan di bagian dalam pipi mulut',
            'Pembengkakan kelenjar getah bening leher belakang/telinga',
            'Pola penyebaran ruam merah berawal dari wajah/leher turun ke badan',
            'Rasa nyeri atau pegal pada persendian tubuh',
            'Adanya ruam lepuhan gelembung berisi cairan tipis gatal',
            'Menurunnya keinginan untuk makan',
            'Kondisi tubuh terasa letih, lesu, dan lemas'
        ]
    }
    st.dataframe(pd.DataFrame(fitur_data), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# MAIN APP ENTRY
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Deteksi Penyakit Ruam Kulit",
        page_icon="🔬",
        layout="wide"
    )

    apply_premium_styles()

    st.markdown(
        """
        <div class="app-title-container">
            <h1 class="app-title">🔬 Sistem Klasifikasi Ruam Kulit</h1>
            <div class="app-subtitle">
                Aplikasi Akademis Klasifikasi Campak, Rubella, dan Cacar Air menggunakan <strong>Multi-Modal Deep Learning (CNN + MLP)</strong>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    tab_dash, tab_pred, tab_about = st.tabs([
        "📊 Dashboard Data & Performa", 
        "🔍 Deteksi & Diagnosis", 
        "ℹ️ Detail Arsitektur Model"
    ])

    with tab_dash:
        show_dashboard_page()

    with tab_pred:
        show_prediction_page()

    with tab_about:
        show_about_page()

    st.markdown(
        """
        <hr style="margin-top: 3rem; border: 0; border-top: 1px solid #eee;">
        <div style="text-align: center; color: #888; font-size: 0.85rem; padding-bottom: 1.5rem;">
            Sistem Deteksi Ruam Kulit (Multimodal Late Fusion Network) | Tugas Penelitian Ilmiah | © 2026
        </div>
        """, unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()
