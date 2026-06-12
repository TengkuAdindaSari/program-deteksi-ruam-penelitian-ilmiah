"""
routes/user.py — Profil User
Endpoint: /api/user/profile
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models import User, Diagnosis

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Ambil profil user."""
    identity = get_jwt_identity()
    user     = User.query.get(identity)

    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    # Hitung statistik diagnosis
    total     = Diagnosis.query.filter_by(user_id=user.id).count()
    campak    = Diagnosis.query.filter_by(user_id=user.id, hasil='campak').count()
    rubella   = Diagnosis.query.filter_by(user_id=user.id, hasil='rubella').count()
    cacar     = Diagnosis.query.filter_by(user_id=user.id, hasil='cacar').count()

    data = user.to_dict()
    data['statistik'] = {
        'total_diagnosis': total,
        'campak'         : campak,
        'rubella'        : rubella,
        'cacar'          : cacar,
    }

    return jsonify({'success': True, 'data': data}), 200


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update nama user."""
    identity = get_jwt_identity()
    user     = User.query.get(identity)
    data     = request.get_json()

    if data.get('nama'):
        user.nama = data['nama']

    db.session.commit()
    return jsonify({'success': True, 'message': 'Profil diperbarui', 'data': user.to_dict()}), 200


@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_user():
    """Data dashboard user — ringkasan diagnosis."""
    identity = get_jwt_identity()
    user_id  = identity

    diagnoses = Diagnosis.query\
        .filter_by(user_id=user_id)\
        .filter(Diagnosis.status != 'dihapus')\
        .order_by(Diagnosis.created_at.desc())\
        .limit(5).all()

    total   = Diagnosis.query.filter_by(user_id=user_id).count()
    campak  = Diagnosis.query.filter_by(user_id=user_id, hasil='campak').count()
    rubella = Diagnosis.query.filter_by(user_id=user_id, hasil='rubella').count()
    cacar   = Diagnosis.query.filter_by(user_id=user_id, hasil='cacar').count()

    return jsonify({
        'success': True,
        'data'   : {
            'statistik': {
                'total'  : total,
                'campak' : campak,
                'rubella': rubella,
                'cacar'  : cacar,
            },
            'riwayat_terbaru': [d.to_dict() for d in diagnoses],
        }
    }), 200
