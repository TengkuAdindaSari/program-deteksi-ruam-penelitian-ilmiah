"""
streamlit_app.py
================
Visualisasi hasil training dan evaluasi model menggunakan Streamlit.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import os
import sys
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

# ── Path ──
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)
MODEL_DIR = os.path.join(ROOT_DIR, 'model')
DATA_DIR  = os.path.join(ROOT_DIR, 'data')

from preprocessing import load_data

# ── Konfigurasi Streamlit ──
st.set_page_config(
    page_title="Model Deteksi Ruam",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Custom ──
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    h2 {
        color: #1f77b4;
        margin-top: 2rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def align_symptom_data(X_sym, target_size):
    """Sejajarkan jumlah sampel gejala dengan citra."""
    if len(X_sym) == target_size:
        return X_sym
    elif len(X_sym) < target_size:
        n_repeats = target_size // len(X_sym) + 1
        X_sym_repeated = np.tile(X_sym, (n_repeats, 1))
        return X_sym_repeated[:target_size]
    else:
        return X_sym[:target_size]


@st.cache_resource
def load_model():
    """Load model dengan caching."""
    model_path = os.path.join(MODEL_DIR, 'best_model.keras')
    if os.path.exists(model_path):
        return tf.keras.models.load_model(model_path)
    return None


@st.cache_data
def load_training_data():
    """Load data dengan caching."""
    return load_data(DATA_DIR)


def display_header():
    """Tampilkan header aplikasi."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        # 🏥 Model Deteksi Penyakit Ruam Kulit
        **Multimodal Deep Learning: CNN + MLP**
        
        Klasifikasi 3 penyakit: Campak, Rubella, Cacar Air
        """)
    st.divider()


def display_model_info():
    """Tampilkan informasi model."""
    st.subheader("📊 Informasi Model")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Model Type", "Fusion Network")
    with col2:
        st.metric("Total Parameter", "2,652,195")
    with col3:
        st.metric("Classes", "3")
    
    st.info("""
    **Arsitektur:**
    - **CNN Branch:** MobileNetV2 (pretrained ImageNet)
    - **MLP Branch:** Gejala klinis (6 fitur)
    - **Fusion Layer:** Concatenation + Dense layers
    
    **Training Phases:**
    - Phase 1: 25 epochs (backbone frozen, val_acc: 96.98%)
    - Phase 2: 7 epochs (fine-tuning, val_acc: 95.48%)
    
    **Final Results:**
    - Test Accuracy: **93.17%** ✅
    - Test Loss: **0.1695** ✅
    """)


def display_dataset_info():
    """Tampilkan informasi dataset."""
    st.subheader("📁 Ringkasan Dataset")
    
    try:
        data = load_training_data()
        img_data = data['images']
        sym_data = data['symptoms']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Training Samples", len(img_data['y_train']))
        with col2:
            st.metric("Validation Samples", len(img_data['y_val']))
        with col3:
            st.metric("Test Samples", len(img_data['y_test']))
        
        # Distribution
        st.write("**Distribusi Kelas (Training):**")
        classes = ['Campak', 'Rubella', 'Cacar']
        class_counts = [660, 558, 900]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        ax.bar(classes, class_counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Jumlah Gambar', fontsize=12, fontweight='bold')
        ax.set_title('Distribusi Kelas Training Data', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for i, v in enumerate(class_counts):
            ax.text(i, v + 20, str(v), ha='center', fontweight='bold')
        
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")


def display_evaluation_results():
    """Tampilkan hasil evaluasi."""
    st.subheader("🎯 Hasil Evaluasi Test Set")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Test Accuracy", "93.17%", "+8.29%")
        st.metric("Test Loss", "0.1695")
    
    with col2:
        st.metric("Precision (Weighted)", "0.93")
        st.metric("Recall (Weighted)", "0.93")
    
    # Classification Report
    st.write("**Classification Report:**")
    
    report_data = {
        'Class': ['Campak', 'Rubella', 'Cacar', 'Weighted Avg'],
        'Precision': [0.94, 0.50, 0.97, 0.93],
        'Recall': [0.89, 0.56, 0.99, 0.93],
        'F1-Score': [0.91, 0.53, 0.98, 0.93],
        'Support': [83, 9, 113, 205]
    }
    
    df_report = pd.DataFrame(report_data)
    st.dataframe(df_report, use_container_width=True, hide_index=True)


def display_confusion_matrix():
    """Tampilkan confusion matrix."""
    st.subheader("🔍 Confusion Matrix")
    
    cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')
    
    if os.path.exists(cm_path):
        img = Image.open(cm_path)
        st.image(img, use_column_width=True, caption="Test Set Confusion Matrix")
    else:
        st.warning("Confusion matrix image tidak ditemukan")


def display_training_history():
    """Tampilkan grafik training history."""
    st.subheader("📈 Training History")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Phase 1: Frozen Backbone**")
        phase1_path = os.path.join(MODEL_DIR, 'history_phase1_frozen.png')
        if os.path.exists(phase1_path):
            img1 = Image.open(phase1_path)
            st.image(img1, use_column_width=True)
        else:
            st.info("History Phase 1 belum tersedia")
    
    with col2:
        st.write("**Phase 2: Fine-tuning**")
        phase2_path = os.path.join(MODEL_DIR, 'history_phase2_finetune.png')
        if os.path.exists(phase2_path):
            img2 = Image.open(phase2_path)
            st.image(img2, use_column_width=True)
        else:
            st.info("History Phase 2 belum tersedia")


def display_performance_metrics():
    """Tampilkan metrik performa per kelas."""
    st.subheader("⭐ Performa Per Kelas")
    
    metrics_data = {
        'Class': ['Campak', 'Rubella', 'Cacar'],
        'Precision': [0.94, 0.50, 0.97],
        'Recall': [0.89, 0.56, 0.99],
        'F1-Score': [0.91, 0.53, 0.98]
    }
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    x = np.arange(len(metrics_data['Class']))
    width = 0.25
    
    bars1 = ax.bar(x - width, metrics_data['Precision'], width, label='Precision', color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x, metrics_data['Recall'], width, label='Recall', color='#4ECDC4', alpha=0.8)
    bars3 = ax.bar(x + width, metrics_data['F1-Score'], width, label='F1-Score', color='#45B7D1', alpha=0.8)
    
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Performa Metrik Per Kelas', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_data['Class'])
    ax.legend(fontsize=10)
    ax.set_ylim([0, 1.0])
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    st.pyplot(fig)


def display_test_accuracy_chart():
    """Tampilkan chart akurasi per kelas."""
    st.subheader("✅ Accuracy Per Class")
    
    accuracy_data = {
        'Class': ['Campak', 'Rubella', 'Cacar'],
        'Accuracy': [89, 56, 99]
    }
    
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    bars = ax.barh(accuracy_data['Class'], accuracy_data['Accuracy'], color=colors, alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Recall (%)', fontsize=12, fontweight='bold')
    ax.set_title('Test Set Recall per Kelas', fontsize=14, fontweight='bold')
    ax.set_xlim([0, 100])
    ax.grid(axis='x', alpha=0.3)
    
    for i, (bar, val) in enumerate(zip(bars, accuracy_data['Accuracy'])):
        ax.text(val + 2, i, f'{val}%', va='center', fontweight='bold')
    
    st.pyplot(fig)


def display_summary():
    """Tampilkan ringkasan."""
    st.subheader("📋 Ringkasan")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.write("""
        ### ✅ Keunggulan Model
        - Akurasi test set: **93.17%** 🚀
        - F1-Score Cacar: **0.98** (outstanding)
        - Recall Cacar: **99%** (nearly perfect)
        - F1-Score Campak: **0.91** (excellent)
        - Precision Cacar: **0.97** (very high)
        - Multimodal approach (citra + gejala)
        """)
    
    with summary_col2:
        st.write("""
        ### 📊 Performa Per Kelas
        - **Cacar**: Precision 0.97, Recall 0.99 ⭐ (best)
        - **Campak**: Precision 0.94, Recall 0.89 ✅ (good)
        - **Rubella**: Precision 0.50, Recall 0.56 ⚠️ (limited data)
        - Test set 205 sampel: 83 Campak, 9 Rubella, 113 Cacar
        - Unbalanced distribution mempengaruhi Rubella
        - Model excel dalam mendeteksi Cacar
        """)
    
    st.info("""
    **Output Model:**
    - 📁 best_model.keras - Model terbaik
    - 📁 final_model.keras - Model final
    - 📊 evaluation_report.txt - Laporan evaluasi
    - 🖼️ confusion_matrix.png - Confusion matrix
    - 📈 history_phase1_frozen.png - Training history fase 1
    - 📈 history_phase2_finetune.png - Training history fase 2
    """)


def main():
    """Main aplikasi."""
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.header("📌 Navigasi")
        page = st.radio(
            "Pilih halaman:",
            ["Overview", "Dataset", "Evaluasi", "Training History", "Performa Metrik", "Ringkasan"]
        )
    
    # Main content
    if page == "Overview":
        display_model_info()
        st.divider()
        display_dataset_info()
    
    elif page == "Dataset":
        display_dataset_info()
    
    elif page == "Evaluasi":
        display_evaluation_results()
        st.divider()
        display_confusion_matrix()
    
    elif page == "Training History":
        display_training_history()
    
    elif page == "Performa Metrik":
        display_performance_metrics()
        st.divider()
        display_test_accuracy_chart()
    
    elif page == "Ringkasan":
        display_summary()
    
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em; margin-top: 2rem;'>
    <p>🏥 Program Deteksi Ruam - Penelitian Ilmiah | 2026</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
