"""
routes/auth.py — Autentikasi
Endpoint: /api/auth/register, /login, /logout, /me
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint('auth', __name__)

# Token blacklist sederhana (gunakan Redis di production)
blacklisted_tokens = set()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Daftar user baru."""
    data = request.get_json()

    # Validasi field
    required = ['nama', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} wajib diisi'}), 400

    # Cek email sudah terdaftar
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email sudah terdaftar'}), 409

    # Hash password
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    user = User(
        nama     = data['nama'],
        email    = data['email'],
        password = hashed,
        role     = 'user',  # default user, admin hanya bisa dibuat dari admin panel
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registrasi berhasil',
        'data'   : user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user atau admin."""
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Email dan password wajib diisi'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'success': False, 'message': 'Email atau password salah'}), 401

    # Buat JWT token
    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'email': user.email,
            'role' : user.role,
        }
    )

    return jsonify({
        'success': True,
        'message': 'Login berhasil',
        'token'  : token,
        'user'   : user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Ambil data user yang sedang login."""
    identity = get_jwt_identity()
    user = User.query.get(identity)

    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    return jsonify({'success': True, 'data': user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout — blacklist token."""
    jti = get_jwt()['jti']
    blacklisted_tokens.add(jti)
    return jsonify({'success': True, 'message': 'Logout berhasil'}), 200


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Ganti password user."""
    identity = get_jwt_identity()
    data     = request.get_json()
    user     = User.query.get(identity)

    if not bcrypt.check_password_hash(user.password, data.get('password_lama', '')):
        return jsonify({'success': False, 'message': 'Password lama salah'}), 400

    if not data.get('password_baru'):
        return jsonify({'success': False, 'message': 'Password baru wajib diisi'}), 400

    user.password = bcrypt.generate_password_hash(data['password_baru']).decode('utf-8')
    db.session.commit()

    return jsonify({'success': True, 'message': 'Password berhasil diubah'}), 200
