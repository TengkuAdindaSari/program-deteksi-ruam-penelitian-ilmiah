from app import create_app
from extensions import db, bcrypt
from models import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email='admin@dermdetect.com').first()
    if not admin:
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(nama='Administrator', email='admin@dermdetect.com', password=hashed, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Berhasil: Akun Admin telah dibuat!")
    else:
        admin.password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin.role = 'admin'
        db.session.commit()
        print("✅ Berhasil: Password Admin telah direset ke 'admin123'!")
