"""
config.py — Konfigurasi Flask
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY          = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG               = os.getenv('FLASK_DEBUG', 'True') == 'True'

    # MySQL via SQLAlchemy
    DB_HOST             = os.getenv('DB_HOST', 'localhost')
    DB_PORT             = os.getenv('DB_PORT', '3306')
    DB_NAME             = os.getenv('DB_NAME', 'dermdetect')
    DB_USER             = os.getenv('DB_USER', 'root')
    DB_PASSWORD         = os.getenv('DB_PASSWORD', '')

    import urllib.parse
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY              = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES    = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    )

    # Upload
    UPLOAD_FOLDER       = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH  = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS  = {'jpg', 'jpeg', 'png', 'bmp'}

    # Model
    MODEL_PATH          = os.getenv('MODEL_PATH', '../model/best_model.keras')
