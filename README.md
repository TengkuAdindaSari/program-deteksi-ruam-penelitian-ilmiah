# DermDetect — Sistem Klasifikasi Penyakit Ruam Kulit

DermDetect adalah aplikasi berbasis web yang digunakan untuk mengklasifikasikan penyakit ruam kulit (seperti Campak, Rubella, dan Cacar Air) menggunakan 3 metode prediksi sekaligus (**Triple Result Diagnosis**):
1. **CNN Only** — Klasifikasi berdasarkan foto ruam saja.
2. **MLP Only** — Klasifikasi berdasarkan gejala klinis saja.
3. **Fusion (Utama)** — Klasifikasi gabungan citra (CNN) dan gejala klinis (MLP) dengan tingkat akurasi tertinggi.

Aplikasi ini menggunakan **Flask** sebagai REST API backend (TensorFlow/Keras model) dan **PHP (Vanilla CSS/HTML5/JavaScript)** sebagai frontend.

---

## 📋 Prasyarat Sistem
Sebelum menjalankan aplikasi, pastikan sistem Anda telah terinstal:
- **Python 3.10** atau versi lebih baru
- **PHP 8.0** atau versi lebih baru (dengan ekstensi `php-curl` aktif)
- **MySQL Server**
- **ngrok** (opsional, untuk online sharing/publikasi port)

---

## 🛠️ Langkah-Langkah Instalasi & Setup

### 1. Setup Database MySQL
1. Buat database baru bernama `dermdetect` di MySQL Anda.
2. Impor berkas struktur database yang terletak di:
   ```bash
   flask-backend/database.sql
   ```
   *Tip: File SQL tersebut sudah terisi user default Administrator (`admin@dermdetect.com` / `admin123`) serta metadata model aktif.*

### 2. Setup Flask Backend (Python)
1. Buka terminal lalu masuk ke direktori `flask-backend`:
   ```bash
   cd flask-backend
   ```
2. Buat Virtual Environment baru (disarankan):
   ```bash
   python -m venv venv
   ```
3. Aktifkan virtual environment:
   - **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
4. Instal semua dependensi python yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
5. Buat dan sesuaikan konfigurasi berkas `.env` di dalam folder `flask-backend`:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=mysql+pymysql://username_db:password_db@localhost/dermdetect
   SECRET_KEY=isi_random_secret_key
   JWT_SECRET_KEY=isi_random_jwt_secret_key
   UPLOAD_FOLDER=static/uploads
   ```

---

## 🚀 Cara Menjalankan Program

Untuk menjalankan DermDetect secara utuh, Anda perlu mengaktifkan **Backend Flask** dan **Frontend PHP** secara bersamaan.

### A. Jalankan Flask Backend
1. Pastikan virtual environment dalam keadaan aktif.
2. Jalankan perintah:
   ```bash
   python app.py
   ```
   Backend akan berjalan secara default di `http://127.0.0.1:5000`.

### B. Jalankan PHP Frontend
1. Buka terminal baru lalu masuk ke direktori frontend:
   ```bash
   cd "frontend - php"
   ```
2. Pastikan file symlink `includes` sudah dibuat untuk mengatasi pemanggilan folder `include`:
   - **Linux/macOS**:
     ```bash
     ln -s include includes
     ```
   - **Windows (Command Prompt Administrator)**:
     ```cmd
     mklink /D includes include
     ```
3. Jalankan PHP Built-in Server pada port `8080`:
   ```bash
   php -S localhost:8080
   ```
4. Buka browser dan akses **`http://localhost:8080`** untuk masuk ke aplikasi.

---

## 🌐 Cara Membagikan Aplikasi ke Publik dengan ngrok

**ngrok** memungkinkan Anda untuk mengekspos localhost agar bisa diakses oleh orang lain melalui internet (luar jaringan lokal) secara gratis.

> [!NOTE]
> Karena Frontend PHP melakukan panggilan API ke Flask backend di sisi server (server-side cURL), Anda **hanya perlu mengekspos port Frontend PHP (8080)** ke publik. Permintaan API ke Flask (port 5000) akan berjalan secara internal di server lokal Anda.

### Langkah-langkah Ekspos dengan ngrok:

1. **Unduh dan Instal ngrok**:
   Unduh versi ngrok yang sesuai untuk OS Anda di [ngrok.com](https://ngrok.com/).

2. **Daftarkan Authtoken Anda**:
   Dapatkan authtoken gratis dari dashboard ngrok Anda, lalu jalankan di terminal:
   ```bash
   ngrok config add-authtoken <TOKEN_ANDA>
   ```

3. **Jalankan ngrok Tunnel untuk Port PHP (8080)**:
   Jalankan perintah berikut di terminal:
   ```bash
   ngrok http 8080
   ```

4. **Dapatkan URL Publik**:
   Terminal ngrok akan menampilkan informasi tunnel yang aktif. Cari bagian **Forwarding**:
   ```text
   Forwarding   https://a1b2-34-56-78.ngrok-free.app -> http://localhost:8080
   ```
   Gunakan URL HTTPS dari ngrok tersebut (`https://a1b2-34-56-78.ngrok-free.app`) untuk dibagikan kepada penguji/publik. Aplikasi Anda sekarang sudah bisa diakses dari smartphone, tablet, atau perangkat eksternal lainnya melalui internet!
