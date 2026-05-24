"""
routes/admin.py — Panel Admin
Endpoint: /api/admin/...

Semua endpoint membutuhkan role admin.
"""

import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from sqlalchemy import func

from extensions import db, bcrypt
from models import User, Diagnosis, ModelVersion

admin_bp = Blueprint('admin', __name__)


# ─────────────────────────────────────────────
# DECORATOR: Cek role admin
# ─────────────────────────────────────────────

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Akses ditolak — hanya admin'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# DASHBOARD ADMIN
# ─────────────────────────────────────────────

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """Statistik keseluruhan untuk admin."""
    total_diagnosis = Diagnosis.query.count()
    total_user      = User.query.filter_by(role='user').count()
    campak_count    = Diagnosis.query.filter_by(hasil='campak').count()
    rubella_count   = Diagnosis.query.filter_by(hasil='rubella').count()
    cacar_count     = Diagnosis.query.filter_by(hasil='cacar').count()
    review_count    = Diagnosis.query.filter_by(status='review').count()

    model_aktif = ModelVersion.query.filter_by(is_active=True).first()

    # Diagnosis 7 hari terakhir per hari
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    tren  = []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        count = Diagnosis.query.filter(
            func.date(Diagnosis.created_at) == day
        ).count()
        tren.append({'tanggal': day.isoformat(), 'jumlah': count})

    return jsonify({
        'success': True,
        'data'   : {
            'total_diagnosis': total_diagnosis,
            'total_user'     : total_user,
            'review_pending' : review_count,
            'distribusi': {
                'campak' : campak_count,
                'rubella': rubella_count,
                'cacar'  : cacar_count,
            },
            'model_aktif': model_aktif.to_dict() if model_aktif else None,
            'tren_7_hari': tren,
        }
    }), 200


# ─────────────────────────────────────────────
# KELOLA HISTORI DIAGNOSIS
# ─────────────────────────────────────────────

@admin_bp.route('/diagnoses', methods=['GET'])
@admin_required
def all_diagnoses():
    """Semua histori diagnosis dengan filter & pagination."""
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    hasil    = request.args.get('hasil')       # campak/rubella/cacar
    status   = request.args.get('status')      # selesai/review/dihapus
    keyword  = request.args.get('keyword')     # cari nama user

    query = Diagnosis.query.join(User, Diagnosis.user_id == User.id)

    if hasil:
        query = query.filter(Diagnosis.hasil == hasil)
    if status:
        query = query.filter(Diagnosis.status == status)
    if keyword:
        query = query.filter(User.nama.ilike(f'%{keyword}%'))

    paginated = query.order_by(Diagnosis.created_at.desc())\
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


@admin_bp.route('/diagnoses/<int:diagnosis_id>', methods=['GET'])
@admin_required
def get_diagnosis(diagnosis_id):
    """Detail satu diagnosis."""
    d = Diagnosis.query.get_or_404(diagnosis_id)
    return jsonify({'success': True, 'data': d.to_dict()}), 200


@admin_bp.route('/diagnoses/<int:diagnosis_id>/status', methods=['PUT'])
@admin_required
def update_status(diagnosis_id):
    """Update status diagnosis (selesai/review/dihapus)."""
    d    = Diagnosis.query.get_or_404(diagnosis_id)
    data = request.get_json()

    allowed = ['selesai', 'review', 'dihapus']
    if data.get('status') not in allowed:
        return jsonify({'success': False, 'message': f'Status harus: {allowed}'}), 400

    d.status = data['status']
    db.session.commit()

    return jsonify({'success': True, 'message': 'Status diperbarui', 'data': d.to_dict()}), 200


@admin_bp.route('/diagnoses/<int:diagnosis_id>', methods=['DELETE'])
@admin_required
def delete_diagnosis(diagnosis_id):
    """Hapus permanen satu diagnosis."""
    d = Diagnosis.query.get_or_404(diagnosis_id)
    db.session.delete(d)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Diagnosis dihapus permanen'}), 200


# ─────────────────────────────────────────────
# KELOLA USER
# ─────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@admin_required
def all_users():
    """Daftar semua user."""
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword  = request.args.get('keyword')

    query = User.query
    if keyword:
        query = query.filter(
            User.nama.ilike(f'%{keyword}%') | User.email.ilike(f'%{keyword}%')
        )

    paginated = query.order_by(User.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)

    # Tambah jumlah diagnosis per user
    result = []
    for u in paginated.items:
        data = u.to_dict()
        data['total_diagnosis'] = Diagnosis.query.filter_by(user_id=u.id).count()
        result.append(data)

    return jsonify({
        'success': True,
        'data'   : result,
        'meta'   : {
            'page'    : paginated.page,
            'per_page': paginated.per_page,
            'total'   : paginated.total,
            'pages'   : paginated.pages,
        }
    }), 200


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Tambah user baru (bisa set role admin)."""
    data = request.get_json()

    required = ['nama', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} wajib diisi'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email sudah terdaftar'}), 409

    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user   = User(
        nama     = data['nama'],
        email    = data['email'],
        password = hashed,
        role     = data.get('role', 'user'),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'User berhasil dibuat', 'data': user.to_dict()}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Edit nama, email, atau role user."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if data.get('nama'):
        user.nama = data['nama']
    if data.get('email'):
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'success': False, 'message': 'Email sudah dipakai'}), 409
        user.email = data['email']
    if data.get('role') in ['user', 'admin']:
        user.role = data['role']
    if data.get('password'):
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    db.session.commit()
    return jsonify({'success': True, 'message': 'User diperbarui', 'data': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Hapus user beserta seluruh diagnosisnya."""
    identity = get_jwt_identity()
    if str(user_id) == str(identity):
        return jsonify({'success': False, 'message': 'Tidak bisa menghapus akun sendiri'}), 400

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User dihapus'}), 200


# ─────────────────────────────────────────────
# KELOLA MODEL
# ─────────────────────────────────────────────

@admin_bp.route('/models', methods=['GET'])
@admin_required
def all_models():
    """Daftar semua versi model."""
    models = ModelVersion.query.order_by(ModelVersion.created_at.desc()).all()
    return jsonify({'success': True, 'data': [m.to_dict() for m in models]}), 200


@admin_bp.route('/models/upload', methods=['POST'])
@admin_required
def upload_model():
    """Upload file model .keras baru."""
    identity = get_jwt_identity()

    if 'model_file' not in request.files:
        return jsonify({'success': False, 'message': 'File model wajib diupload'}), 400

    file = request.files['model_file']
    if not file.filename.endswith('.keras') and not file.filename.endswith('.h5'):
        return jsonify({'success': False, 'message': 'Format file harus .keras atau .h5'}), 400

    # Simpan file model
    ext       = file.filename.rsplit('.', 1)[1].lower()
    filename  = f"model_{uuid.uuid4().hex[:8]}.{ext}"
    model_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..', 'model'
    )
    os.makedirs(model_dir, exist_ok=True)
    file.save(os.path.join(model_dir, filename))

    # Simpan ke database
    data    = request.form
    version = ModelVersion(
        versi       = data.get('versi', 'v_baru'),
        nama_file   = filename,
        akurasi     = float(data.get('akurasi', 0)) if data.get('akurasi') else None,
        f1_score    = float(data.get('f1_score', 0)) if data.get('f1_score') else None,
        keterangan  = data.get('keterangan'),
        is_active   = False,
        uploaded_by = identity,
    )
    db.session.add(version)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Model berhasil diupload',
        'data'   : version.to_dict()
    }), 201


@admin_bp.route('/models/<int:model_id>/activate', methods=['PUT'])
@admin_required
def activate_model(model_id):
    """Aktifkan satu model, nonaktifkan yang lain."""
    # Nonaktifkan semua model
    ModelVersion.query.update({'is_active': False})

    # Aktifkan model yang dipilih
    model = ModelVersion.query.get_or_404(model_id)
    model.is_active = True
    db.session.commit()

    # Reset cache model
    from routes.diagnose import _model_cache
    _model_cache.clear()

    return jsonify({
        'success': True,
        'message': f'Model {model.versi} diaktifkan',
        'data'   : model.to_dict()
    }), 200


@admin_bp.route('/models/<int:model_id>', methods=['DELETE'])
@admin_required
def delete_model(model_id):
    """Hapus versi model (tidak bisa hapus model aktif)."""
    model = ModelVersion.query.get_or_404(model_id)

    if model.is_active:
        return jsonify({'success': False, 'message': 'Tidak bisa menghapus model yang sedang aktif'}), 400

    # Hapus file fisik
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..', 'model', model.nama_file
    )
    if os.path.exists(model_path):
        os.remove(model_path)

    db.session.delete(model)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Model dihapus'}), 200


# ─────────────────────────────────────────────
# STATISTIK
# ─────────────────────────────────────────────

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def stats():
    """Statistik lengkap untuk grafik admin."""
    from datetime import datetime, timedelta

    # Distribusi per kelas
    campak  = Diagnosis.query.filter_by(hasil='campak').count()
    rubella = Diagnosis.query.filter_by(hasil='rubella').count()
    cacar   = Diagnosis.query.filter_by(hasil='cacar').count()

    # Rata-rata confidence per kelas
    avg_conf_campak  = db.session.query(func.avg(Diagnosis.confidence))\
                                 .filter_by(hasil='campak').scalar() or 0
    avg_conf_rubella = db.session.query(func.avg(Diagnosis.confidence))\
                                 .filter_by(hasil='rubella').scalar() or 0
    avg_conf_cacar   = db.session.query(func.avg(Diagnosis.confidence))\
                                 .filter_by(hasil='cacar').scalar() or 0

    # Tren 30 hari terakhir
    today = datetime.utcnow().date()
    tren  = []
    for i in range(29, -1, -1):
        day   = today - timedelta(days=i)
        count = Diagnosis.query.filter(
            func.date(Diagnosis.created_at) == day
        ).count()
        tren.append({'tanggal': day.isoformat(), 'jumlah': count})

    return jsonify({
        'success': True,
        'data'   : {
            'distribusi': {
                'campak' : campak,
                'rubella': rubella,
                'cacar'  : cacar,
            },
            'avg_confidence': {
                'campak' : round(avg_conf_campak  * 100, 2),
                'rubella': round(avg_conf_rubella * 100, 2),
                'cacar'  : round(avg_conf_cacar   * 100, 2),
            },
            'tren_30_hari': tren,
        }
    }), 200
