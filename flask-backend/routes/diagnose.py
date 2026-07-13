"""
routes/diagnose.py — Endpoint Prediksi Triple Result
=====================================================
Menghasilkan 3 hasil diagnosis sekaligus:
  1. CNN Only  — berdasarkan foto saja
  2. MLP Only  — berdasarkan gejala saja
  3. Fusion    — gabungan foto + gejala (hasil utama)
"""

import os
import uuid
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from PIL import Image
import tensorflow as tf
import pickle

from extensions import db
from models import Diagnosis, ModelVersion

diagnose_bp = Blueprint('diagnose', __name__)

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.50   # threshold minimal untuk fusion

# ─────────────────────────────────────────────
# HELPER: PARSE JWT IDENTITY
# ─────────────────────────────────────────────
def parse_identity(raw):
    """JWT identity bisa dict, string, atau integer tergantung versi."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, int):
        return {'id': raw, 'role': 'user'}
    import json
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        else:
            return {'id': int(parsed), 'role': 'user'}
    except Exception:
        return {'id': int(raw) if str(raw).isdigit() else raw, 'role': 'user'}

CLASSES      = ['campak', 'rubella', 'cacar']
CLASSES_DISP = ['Campak', 'Rubella', 'Cacar Air']

_model_cache = {}
# Cache dictionary untuk Random Forest model agar tidak dimuat berulang kali
_rf_cache   = {}


def get_rf_model():
    """Load Random Forest model dari file pkl."""
    import os
    rf_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..', 'model', 'rf_model.pkl'
    ))
    if 'rf' not in _rf_cache:
        if not os.path.exists(rf_path):
            return None
        with open(rf_path, 'rb') as f:
            _rf_cache['rf'] = pickle.load(f)
        print('[MODEL] RF loaded')
    return _rf_cache.get('rf')


# ─────────────────────────────────────────────
# HELPER: LOAD MODEL
# ─────────────────────────────────────────────

def get_active_model():
    active = ModelVersion.query.filter_by(is_active=True).first()
    if not active:
        return None, None

    if active.id not in _model_cache:
        model_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '..', 'model', active.nama_file
        ))
        if not os.path.exists(model_path):
            return None, active
        _model_cache[active.id] = tf.keras.models.load_model(model_path)
        print(f"[MODEL] Loaded: {active.nama_file} (v{active.versi})")

    return _model_cache[active.id], active


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# ─────────────────────────────────────────────
# PREPROCESSING
# ─────────────────────────────────────────────

def preprocess_image(filepath: str) -> np.ndarray:
    """Baca gambar → resize 224×224 → normalisasi."""
    img = Image.open(filepath).convert('RGB').resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)   # (1, 224, 224, 3)


def preprocess_symptoms(data) -> np.ndarray:
    """
    Susun vektor gejala klinis (1, 10) sesuai dataset terbaru.
    Kolom: demam_tinggi, demam_ringan, koplik_spot,
           kelenjar_bengkak, vesikel, konjungtivitis, nyeri_sendi,
           sakit_tenggorokan, lemas_malaise, pola_ruam
    """
    return np.array([[
        int(data.get('demam_tinggi',      0)),
        int(data.get('demam_ringan',      0)),
        int(data.get('koplik_spot',       0)),
        int(data.get('kelenjar_bengkak',  0)),
        int(data.get('vesikel',           0)),
        int(data.get('konjungtivitis',    data.get('mata_merah', 0))),
        int(data.get('nyeri_sendi',       0)),
        int(data.get('sakit_tenggorokan', 0)),
        int(data.get('lemas_malaise',     data.get('lemas', 0))),
        1, # pola_ruam di-hardcode ke 1 (karena selalu 100% pada semua kasus)
    ]], dtype=np.float32)


# ─────────────────────────────────────────────
# TRIPLE PREDICTION
# ─────────────────────────────────────────────

def predict_triple(model, img_array: np.ndarray, sym_array: np.ndarray, rf_model=None) -> dict:
    """
    Jalankan 3 prediksi sekaligus:
      1. CNN Only  — foto asli + gejala netral (semua nol)
      2. RF Only   — menggunakan model Random Forest khusus gejala
      3. Fusion    — Average probabilitas CNN + RF
    """

    # ── 1. CNN Only ──
    # Matikan pengaruh gejala dengan vektor nol
    sym_netral = np.zeros_like(sym_array)
    probs_cnn  = model.predict(
        {'input_citra': img_array, 'input_gejala': sym_netral},
        verbose=0
    )[0]

    # ── 2. RF Only ──
    if rf_model is not None:
        rf_probs_raw = rf_model.predict_proba(sym_array)[0]
        rf_classes = list(rf_model.classes_)
        probs_rf = np.zeros(3)
        for i, c in enumerate(CLASSES):
            if c in rf_classes:
                probs_rf[i] = rf_probs_raw[rf_classes.index(c)]
    else:
        # Fallback jika RF tidak ada, pakai MLP
        img_hitam  = np.zeros_like(img_array)
        probs_rf  = model.predict(
            {'input_citra': img_hitam, 'input_gejala': sym_array},
            verbose=0
        )[0]

    # ── 3. Fusion ──
    probs_fusion = (probs_cnn + probs_rf) / 2.0

    def parse_result(probs):
        idx   = int(np.argmax(probs))
        return {
            'prediksi'  : CLASSES[idx],
            'label'     : CLASSES_DISP[idx],
            'confidence': round(float(probs[idx]) * 100, 2),
            'probabilitas': {
                'campak' : round(float(probs[0]) * 100, 2),
                'rubella': round(float(probs[1]) * 100, 2),
                'cacar'  : round(float(probs[2]) * 100, 2),
            }
        }

    cnn    = parse_result(probs_cnn)
    mlp    = parse_result(probs_rf)
    fusion = parse_result(probs_fusion)

    # ── Konsistensi ──
    prediksi_list = [cnn['prediksi'], mlp['prediksi'], fusion['prediksi']]
    unik          = len(set(prediksi_list))

    if unik == 1:
        konsistensi = 'konsisten'
        konsistensi_label = 'Konsisten — Kepercayaan Tinggi'
        konsistensi_icon  = 'success'
    elif unik == 2:
        konsistensi = 'mayoritas'
        konsistensi_label = 'Mayoritas — Disarankan Konsultasi Dokter'
        konsistensi_icon  = 'warning'
    else:
        konsistensi = 'tidak_konsisten'
        konsistensi_label = 'Tidak Konsisten — Wajib Konsultasi Dokter'
        konsistensi_icon  = 'danger'

    return {
        'cnn'   : cnn,
        'mlp'   : mlp,
        'fusion': fusion,
        'konsistensi': {
            'status': konsistensi,
            'label' : konsistensi_label,
            'icon'  : konsistensi_icon,
        }
    }


# ─────────────────────────────────────────────
# ENDPOINT: PREDICT
# ─────────────────────────────────────────────

@diagnose_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Endpoint prediksi triple — menghasilkan 3 hasil sekaligus.
    """
    identity = parse_identity(get_jwt_identity())

    # Validasi foto
    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Foto wajib diupload'}), 400

    file = request.files['foto']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Format foto tidak valid (jpg/png)'}), 400

    # Simpan foto
    ext       = file.filename.rsplit('.', 1)[1].lower()
    filename  = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # Load model
    model, model_version = get_active_model()
    rf_model = get_rf_model()
    if model is None:
        os.remove(save_path)
        return jsonify({'success': False, 'message': 'Model belum tersedia'}), 503

    # Triple prediksi
    try:
        img_array = preprocess_image(save_path)
        sym_array = preprocess_symptoms(request.form)
        triple    = predict_triple(model, img_array, sym_array, rf_model=rf_model)

    except Exception as e:
        os.remove(save_path)
        return jsonify({'success': False, 'message': f'Gagal prediksi: {str(e)}'}), 500

    # Ambil hasil fusion sebagai hasil utama
    fusion     = triple['fusion']
    hasil      = fusion['prediksi']
    confidence = fusion['confidence'] / 100

    # Simpan ke database (simpan hasil fusion sebagai hasil utama)
    diagnosis = Diagnosis(
        user_id          = identity['id'],
        model_id         = model_version.id if model_version else None,
        foto_path        = filename,
        demam_tinggi     = bool(int(request.form.get('demam_tinggi',     0))),
        demam_ringan     = bool(int(request.form.get('demam_ringan',     0))),
        sakit_tenggorokan= bool(int(request.form.get('sakit_tenggorokan',0))),
        konjungtivitis   = bool(int(request.form.get('konjungtivitis',   data.get('mata_merah', 0) if 'data' in locals() else request.form.get('mata_merah', 0)))),
        koplik_spot      = bool(int(request.form.get('koplik_spot',      0))),
        kelenjar_bengkak = bool(int(request.form.get('kelenjar_bengkak', 0))),
        nyeri_sendi      = bool(int(request.form.get('nyeri_sendi',      0))),
        vesikel          = bool(int(request.form.get('vesikel',          0))),
        lemas_malaise    = bool(int(request.form.get('lemas_malaise',     request.form.get('lemas', 0)))),
        hasil            = hasil,
        confidence       = confidence,
        prob_campak      = fusion['probabilitas']['campak']  / 100,
        prob_rubella     = fusion['probabilitas']['rubella'] / 100,
        prob_cacar       = fusion['probabilitas']['cacar']   / 100,
        status           = 'selesai',
    )
    db.session.add(diagnosis)
    db.session.commit()

    # Tambahkan triple result ke response
    result = diagnosis.to_dict()
    result['triple'] = triple

    return jsonify({
        'success': True,
        'message': 'Prediksi berhasil',
        'data'   : result
    }), 200


# ─────────────────────────────────────────────
# ENDPOINT: HISTORY
# ─────────────────────────────────────────────

@diagnose_bp.route('/history', methods=['GET'])
@jwt_required()
def history_user():
    identity = parse_identity(get_jwt_identity())
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated = Diagnosis.query\
        .filter_by(user_id=identity['id'])\
        .filter(Diagnosis.status != 'dihapus')\
        .order_by(Diagnosis.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data'   : [d.to_dict() for d in paginated.items],
        'meta'   : {
            'page'    : paginated.page,
            'per_page': paginated.per_page,
            'total'   : paginated.total,
            'pages'   : paginated.pages,
        }
    }), 200


@diagnose_bp.route('/history/<int:diagnosis_id>', methods=['GET'])
@jwt_required()
def detail_diagnosis(diagnosis_id):
    identity  = parse_identity(get_jwt_identity())
    diagnosis = Diagnosis.query.filter_by(
        id=diagnosis_id, user_id=identity['id']
    ).first()
    if not diagnosis:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404
    return jsonify({'success': True, 'data': diagnosis.to_dict()}), 200


@diagnose_bp.route('/history/<int:diagnosis_id>', methods=['DELETE'])
@jwt_required()
def delete_diagnosis(diagnosis_id):
    identity  = parse_identity(get_jwt_identity())
    diagnosis = Diagnosis.query.filter_by(
        id=diagnosis_id, user_id=identity['id']
    ).first()
    if not diagnosis:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404
    diagnosis.status = 'dihapus'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Diagnosis dihapus'}), 200
