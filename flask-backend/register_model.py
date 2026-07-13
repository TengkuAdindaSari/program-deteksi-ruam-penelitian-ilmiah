import os
import sys

# Tambahkan path flask-backend ke sys.path agar bisa import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import ModelVersion

app = create_app()

def register_model():
    with app.app_context():
        # Set existing active models to False
        active_models = ModelVersion.query.filter_by(is_active=True).all()
        for m in active_models:
            m.is_active = False

        # Check if 'final_model.keras' already exists
        new_model = ModelVersion.query.filter_by(nama_file='final_model.keras').first()
        if not new_model:
            new_model = ModelVersion(
                versi='2.0',
                nama_file='final_model.keras',
                akurasi=0.95,
                f1_score=0.95,
                keterangan='Model FusionNet Ekstrim dengan augmentasi masif dan fitur klinis yang diperbarui.',
                is_active=True
            )
            db.session.add(new_model)
        else:
            new_model.is_active = True
            new_model.versi = '2.1'
            new_model.akurasi = 0.95
            new_model.keterangan = 'Pembaruan FusionNet (Akurasi Uji: 95%)'

        db.session.commit()
        print("Model final_model.keras berhasil didaftarkan dan diaktifkan di database!")

if __name__ == '__main__':
    register_model()
