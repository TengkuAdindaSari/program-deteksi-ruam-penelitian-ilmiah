"""
app.py — Flask Backend API
==========================
Sistem Klasifikasi Penyakit Ruam Kulit
Endpoint untuk User dan Admin

Jalankan:
    (venv) python app.py
"""

from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt, bcrypt
from routes.auth     import auth_bp
from routes.diagnose import diagnose_bp
from routes.user     import user_bp
from routes.admin    import admin_bp
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Buat folder upload jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp,     url_prefix='/api/auth')
    app.register_blueprint(diagnose_bp, url_prefix='/api/diagnose')
    app.register_blueprint(user_bp,     url_prefix='/api/user')
    app.register_blueprint(admin_bp,    url_prefix='/api/admin')

    # Buat tabel otomatis jika belum ada
    with app.app_context():
        db.create_all()

    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'DermDetect API berjalan'}, 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
