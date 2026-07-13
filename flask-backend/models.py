"""
models.py — Database Models (SQLAlchemy)
"""

from __future__ import annotations
from typing import Any
from extensions import db
from datetime import datetime


class User(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'users'

    id          = db.Column(db.Integer, primary_key=True)
    nama        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), nullable=False, unique=True)
    password    = db.Column(db.String(255), nullable=False)
    role        = db.Column(db.Enum('user', 'admin'), default='user')
    foto_profil = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    diagnoses   = db.relationship('Diagnosis', backref='user', lazy=True,
                                  cascade='all, delete-orphan')

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id'         : self.id,
            'nama'       : self.nama,
            'email'      : self.email,
            'role'       : self.role,
            'foto_profil': self.foto_profil,
            'created_at' : self.created_at.isoformat() if self.created_at else None,
        }


class ModelVersion(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'model_versions'

    id          = db.Column(db.Integer, primary_key=True)
    versi       = db.Column(db.String(20), nullable=False)
    nama_file   = db.Column(db.String(255), nullable=False)
    akurasi     = db.Column(db.Float, nullable=True)
    f1_score    = db.Column(db.Float, nullable=True)
    keterangan  = db.Column(db.Text, nullable=True)
    is_active   = db.Column(db.Boolean, default=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id'         : self.id,
            'versi'      : self.versi,
            'nama_file'  : self.nama_file,
            'akurasi'    : self.akurasi,
            'f1_score'   : self.f1_score,
            'keterangan' : self.keterangan,
            'is_active'  : self.is_active,
            'uploaded_by': self.uploaded_by,
            'created_at' : self.created_at.isoformat() if self.created_at else None,
        }


class Diagnosis(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'diagnoses'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_id         = db.Column(db.Integer, db.ForeignKey('model_versions.id'), nullable=True)
    foto_path        = db.Column(db.String(255), nullable=False)
    # Gejala
    demam_tinggi     = db.Column(db.Boolean, default=False)
    demam_ringan     = db.Column(db.Boolean, default=False)
    sakit_tenggorokan = db.Column(db.Boolean, default=False)
    konjungtivitis   = db.Column(db.Boolean, default=False)
    koplik_spot      = db.Column(db.Boolean, default=False)
    kelenjar_bengkak = db.Column(db.Boolean, default=False)
    nyeri_sendi      = db.Column(db.Boolean, default=False)
    vesikel          = db.Column(db.Boolean, default=False)
    lemas_malaise    = db.Column(db.Boolean, default=False)
    # Hasil
    hasil            = db.Column(db.Enum('campak', 'rubella', 'cacar'), nullable=False)
    confidence       = db.Column(db.Float, nullable=False)
    prob_campak      = db.Column(db.Float, nullable=True)
    prob_rubella     = db.Column(db.Float, nullable=True)
    prob_cacar       = db.Column(db.Float, nullable=True)
    status           = db.Column(db.Enum('selesai', 'review', 'dihapus'), default='selesai')
    triple_data      = db.Column(db.Text, nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        import json
        triple = None
        if self.triple_data:
            try:
                triple = json.loads(self.triple_data)
            except Exception:
                pass
        return {
            'id'              : self.id,
            'user_id'         : self.user_id,
            'user_nama'       : self.user.nama if self.user else None,
            'model_id'        : self.model_id,
            'foto_path'       : self.foto_path,
            'gejala': {
                'demam_tinggi'      : self.demam_tinggi,
                'demam_ringan'      : self.demam_ringan,
                'sakit_tenggorokan' : self.sakit_tenggorokan,
                'konjungtivitis'    : self.konjungtivitis,
                'koplik_spot'       : self.koplik_spot,
                'kelenjar_bengkak'  : self.kelenjar_bengkak,
                'nyeri_sendi'       : self.nyeri_sendi,
                'vesikel'           : self.vesikel,
                'lemas_malaise'     : self.lemas_malaise,
            },
            'hasil'           : self.hasil,
            'confidence'      : round(self.confidence * 100, 2),
            'probabilitas': {
                'campak' : round((self.prob_campak  or 0) * 100, 2),
                'rubella': round((self.prob_rubella or 0) * 100, 2),
                'cacar'  : round((self.prob_cacar   or 0) * 100, 2),
            },
            'status'          : self.status,
            'triple'          : triple,
            'created_at'      : self.created_at.isoformat() if self.created_at else None,
        }
