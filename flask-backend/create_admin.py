from app import create_app
from extensions import db, bcrypt
from models import User

app = create_app()
with app.app_context():
    # Hapus semua akun admin yang ada
    admins = User.query.filter_by(role='admin').all()
    if admins:
        for old_admin in admins:
            print(f"[HAPUS] Menghapus akun admin lama: {old_admin.email} (ID: {old_admin.id})")
            db.session.delete(old_admin)
        db.session.commit()
        print(f"[OK] {len(admins)} akun admin lama berhasil dihapus!")
    else:
        print("[INFO] Tidak ada akun admin lama ditemukan.")

    # Buat akun admin baru
    hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
    new_admin = User(
        nama='Administrator',
        email='admin@dermdetect.com',
        password=hashed,
        role='admin'
    )
    db.session.add(new_admin)
    db.session.commit()

    print("")
    print("=" * 50)
    print("[OK] AKUN ADMIN BARU BERHASIL DIBUAT!")
    print("=" * 50)
    print(f"   Email    : admin@dermdetect.com")
    print(f"   Password : admin123")
    print(f"   Role     : admin")
    print(f"   ID       : {new_admin.id}")
    print("=" * 50)
    print("")
    print("[!] Segera ganti password setelah login!")


