"""
routes/diagnose.py — Endpoint Prediksi
Endpoint: /api/diagnose/predict, /history
"""

import os
import uuid
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from PIL import Image
import tensorflow as tf

from extensions import db
from models import Diagnosis, ModelVersion

diagnose_bp = Blueprint('diagnose', __name__)

# Cache model agar tidak reload setiap request
_model_cache = {}


def get_active_model():
    """Load model aktif dari database. Cache di memory."""
    active = ModelVersion.query.filter_by(is_active=True).first()
    if not active:
        return None, None

    if active.id not in _model_cache:
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '..', 'model', active.nama_file
        )
        model_path = os.path.normpath(model_path)
        if not os.path.exists(model_path):
            return None, active
        _model_cache[active.id] = tf.keras.models.load_model(model_path)
        print(f"[MODEL] Loaded: {active.nama_file} (v{active.versi})")

    return _model_cache[active.id], active


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def preprocess_image(filepath):
    """Load dan preprocess gambar untuk CNN."""
    img = Image.open(filepath).convert('RGB').resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)   # (1, 224, 224, 3)


def preprocess_symptoms(data):
    """Susun fitur gejala menjadi array numpy."""
    durasi      = float(data.get('durasi_demam', 4))
    durasi_norm = (durasi - 4.0) / 1.2
    features = np.array([[
        durasi_norm,
        int(data.get('batuk',            0)),
        int(data.get('mata_merah',       0)),
        int(data.get('kelenjar_bengkak', 0)),
        int(data.get('pola_ruam',        0)),
        int(data.get('vesikel',          0)),
    ]], dtype=np.float32)
    return features   # (1, 6)


CLASSES      = ['campak', 'rubella', 'cacar']
CLASSES_DISP = ['Campak', 'Rubella', 'Cacar Air']


@diagnose_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Endpoint prediksi penyakit ruam kulit.

    Form-data:
        foto            : file gambar
        durasi_demam    : int
        batuk           : 0/1
        mata_merah      : 0/1
        kelenjar_bengkak: 0/1
        pola_ruam       : 0/1
        vesikel         : 0/1
    """
    identity = get_jwt_identity()

    # ── Validasi foto ──
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

    # ── Load model ──
    model, model_version = get_active_model()
    if model is None:
        return jsonify({'success': False, 'message': 'Model belum tersedia'}), 503

    # ── Prediksi ──
    try:
        img_array = preprocess_image(save_path)
        sym_array = preprocess_symptoms(request.form)

        probs    = model.predict(
            {'input_citra': img_array, 'input_gejala': sym_array},
            verbose=0
        )[0]

        pred_idx    = int(np.argmax(probs))
        hasil       = CLASSES[pred_idx]
        confidence  = float(probs[pred_idx])

    except Exception as e:
        return jsonify({'success': False, 'message': f'Gagal prediksi: {str(e)}'}), 500

    # ── Simpan ke database ──
    diagnosis = Diagnosis(
        user_id          = identity,
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
        prob_campak      = float(probs[0]),
        prob_rubella     = float(probs[1]),
        prob_cacar       = float(probs[2]),
        status           = 'selesai',
    )
    db.session.add(diagnosis)
    db.session.commit()

    return jsonify({
        'success'   : True,
        'message'   : 'Prediksi berhasil',
        'data'      : diagnosis.to_dict()
    }), 200


@diagnose_bp.route('/history', methods=['GET'])
@jwt_required()
def history_user():
    """Riwayat diagnosis milik user yang login."""
    identity = get_jwt_identity()
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated = Diagnosis.query\
        .filter_by(user_id=identity)\
        .filter(Diagnosis.status != 'dihapus')\
        .order_by(Diagnosis.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data'   : [d.to_dict() for d in paginated.items],
        'meta'   : {
            'page'      : paginated.page,
            'per_page'  : paginated.per_page,
            'total'     : paginated.total,
            'pages'     : paginated.pages,
        }
    }), 200


@diagnose_bp.route('/history/<int:diagnosis_id>', methods=['GET'])
@jwt_required()
def detail_diagnosis(diagnosis_id):
    """Detail satu hasil diagnosis milik user."""
    identity  = get_jwt_identity()
    diagnosis = Diagnosis.query.filter_by(
        id=diagnosis_id, user_id=identity
    ).first()

    if not diagnosis:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404

    return jsonify({'success': True, 'data': diagnosis.to_dict()}), 200


@diagnose_bp.route('/history/<int:diagnosis_id>', methods=['DELETE'])
@jwt_required()
def delete_diagnosis(diagnosis_id):
    """Hapus (soft delete) satu hasil diagnosis milik user."""
    identity  = get_jwt_identity()
    diagnosis = Diagnosis.query.filter_by(
        id=diagnosis_id, user_id=identity
    ).first()

    if not diagnosis:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404

    diagnosis.status = 'dihapus'
    db.session.commit()

    return jsonify({'success': True, 'message': 'Diagnosis dihapus'}), 200
