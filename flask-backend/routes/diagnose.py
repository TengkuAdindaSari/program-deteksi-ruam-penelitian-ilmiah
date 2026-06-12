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
        val = json.loads(raw)
        if isinstance(val, dict):
            return val
        if isinstance(val, int):
            return {'id': val, 'role': 'user'}
        return {'id': int(val), 'role': 'user'}
    except Exception:
        try:
            return {'id': int(raw), 'role': 'user'}
        except Exception:
            return {'id': raw, 'role': 'user'}


CLASSES      = ['campak', 'rubella', 'cacar']
CLASSES_DISP = ['Campak', 'Rubella', 'Cacar Air']

_model_cache = {}


# ─────────────────────────────────────────────
# HELPER: LOAD MODEL
# ─────────────────────────────────────────────

def get_active_model():
    """Load model aktif dari database. Cache di memory."""
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
    """Susun vektor gejala klinis (1, 6)."""
    durasi_norm = (float(data.get('durasi_demam', 4)) - 4.0) / 1.2
    return np.array([[
        durasi_norm,
        int(data.get('batuk',            0)),
        int(data.get('mata_merah',       0)),
        int(data.get('kelenjar_bengkak', 0)),
        int(data.get('pola_ruam',        0)),
        int(data.get('vesikel',          0)),
    ]], dtype=np.float32)


# ─────────────────────────────────────────────
# TRIPLE PREDICTION
# ─────────────────────────────────────────────

def predict_triple(model, img_array: np.ndarray, sym_array: np.ndarray) -> dict:
    """
    Jalankan 3 prediksi sekaligus:
      1. CNN Only  — foto asli + gejala netral (semua nol)
      2. MLP Only  — foto hitam (nol) + gejala asli
      3. Fusion    — foto asli + gejala asli (hasil utama)

    Return dict berisi probabilitas dan prediksi ketiga metode.
    """

    # ── 1. CNN Only ──
    # Matikan pengaruh gejala dengan vektor nol
    sym_netral = np.zeros_like(sym_array)
    probs_cnn  = model.predict(
        {'input_citra': img_array, 'input_gejala': sym_netral},
        verbose=0
    )[0]

    # ── 2. MLP Only ──
    # Matikan pengaruh foto dengan gambar hitam
    img_hitam  = np.zeros_like(img_array)
    probs_mlp  = model.predict(
        {'input_citra': img_hitam, 'input_gejala': sym_array},
        verbose=0
    )[0]

    # ── 3. Fusion (Normal) ──
    probs_fusion = model.predict(
        {'input_citra': img_array, 'input_gejala': sym_array},
        verbose=0
    )[0]

    def parse_result(probs):
        idx = int(np.argmax(probs))
        return {
            'prediksi'    : CLASSES[idx],
            'label'       : CLASSES_DISP[idx],
            'confidence'  : round(float(probs[idx]) * 100, 2),
            'probabilitas': {
                'campak' : round(float(probs[0]) * 100, 2),
                'rubella': round(float(probs[1]) * 100, 2),
                'cacar'  : round(float(probs[2]) * 100, 2),
            }
        }

    cnn    = parse_result(probs_cnn)
    mlp    = parse_result(probs_mlp)
    fusion = parse_result(probs_fusion)

    # ── Konsistensi ──
    prediksi_list = [cnn['prediksi'], mlp['prediksi'], fusion['prediksi']]
    unik          = len(set(prediksi_list))

    if unik == 1:
        konsistensi       = 'konsisten'
        konsistensi_label = 'Konsisten — Kepercayaan Tinggi'
        konsistensi_icon  = 'success'
    elif unik == 2:
        konsistensi       = 'mayoritas'
        konsistensi_label = 'Mayoritas — Disarankan Konsultasi Dokter'
        konsistensi_icon  = 'warning'
    else:
        konsistensi       = 'tidak_konsisten'
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

    Form-data:
        foto            : file gambar
        durasi_demam    : int
        batuk           : 0/1
        mata_merah      : 0/1
        kelenjar_bengkak: 0/1
        pola_ruam       : 0/1
        vesikel         : 0/1
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
    if model is None:
        os.remove(save_path)
        return jsonify({'success': False, 'message': 'Model belum tersedia'}), 503

    # Triple prediksi
    try:
        img_array = preprocess_image(save_path)
        sym_array = preprocess_symptoms(request.form)
        triple    = predict_triple(model, img_array, sym_array)

    except Exception as e:
        os.remove(save_path)
        return jsonify({'success': False, 'message': f'Gagal prediksi: {str(e)}'}), 500

    # Ambil hasil fusion sebagai hasil utama
    fusion     = triple['fusion']
    hasil      = fusion['prediksi']
    confidence = fusion['confidence'] / 100

    # Simpan ke database (simpan hasil fusion sebagai hasil utama)
    import json
    diagnosis = Diagnosis(
        user_id          = identity['id'],
        model_id         = model_version.id if model_version else None,
        foto_path        = filename,
        durasi_demam     = int(request.form.get('durasi_demam', 4)),
        batuk            = bool(int(request.form.get('batuk',            0))),
        mata_merah       = bool(int(request.form.get('mata_merah',       0))),
        kelenjar_bengkak = bool(int(request.form.get('kelenjar_bengkak', 0))),
        pola_ruam        = bool(int(request.form.get('pola_ruam',        0))),
        vesikel          = bool(int(request.form.get('vesikel',          0))),
        hasil            = hasil,
        confidence       = confidence,
        prob_campak      = fusion['probabilitas']['campak']  / 100,
        prob_rubella     = fusion['probabilitas']['rubella'] / 100,
        prob_cacar       = fusion['probabilitas']['cacar']   / 100,
        status           = 'selesai',
        triple_data      = json.dumps(triple),
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
    """Riwayat diagnosis milik user yang login."""
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
    """Detail satu hasil diagnosis milik user."""
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
    """Hapus (soft delete) satu hasil diagnosis milik user."""
    identity  = parse_identity(get_jwt_identity())
    diagnosis = Diagnosis.query.filter_by(
        id=diagnosis_id, user_id=identity['id']
    ).first()
    if not diagnosis:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404
    diagnosis.status = 'dihapus'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Diagnosis dihapus'}), 200
