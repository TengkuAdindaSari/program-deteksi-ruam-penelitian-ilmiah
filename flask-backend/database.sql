-- ============================================================
-- DATABASE: dermdetect
-- Sistem Klasifikasi Penyakit Ruam Kulit
-- ============================================================

CREATE DATABASE IF NOT EXISTS dermdetect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dermdetect;

-- ─────────────────────────────────────────────
-- TABEL: users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nama        VARCHAR(100)         NOT NULL,
    email       VARCHAR(150)         NOT NULL UNIQUE,
    password    VARCHAR(255)         NOT NULL,
    role        ENUM('user','admin') DEFAULT 'user',
    foto_profil VARCHAR(255)         DEFAULT NULL,
    created_at  DATETIME             DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABEL: model_versions
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_versions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    versi       VARCHAR(20)  NOT NULL,
    nama_file   VARCHAR(255) NOT NULL,
    akurasi     FLOAT        DEFAULT NULL,
    f1_score    FLOAT        DEFAULT NULL,
    keterangan  TEXT         DEFAULT NULL,
    is_active   TINYINT(1)   DEFAULT 0,
    uploaded_by INT          DEFAULT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT          NOT NULL,
    model_id         INT          DEFAULT NULL,
    foto_path        VARCHAR(255) NOT NULL,
    demam_tinggi     TINYINT(1)   DEFAULT 0,
    demam_ringan     TINYINT(1)   DEFAULT 0,
    sakit_tenggorokan TINYINT(1)  DEFAULT 0,
    konjungtivitis   TINYINT(1)   DEFAULT 0,
    koplik_spot      TINYINT(1)   DEFAULT 0,
    kelenjar_bengkak TINYINT(1)   DEFAULT 0,
    nyeri_sendi      TINYINT(1)   DEFAULT 0,
    vesikel          TINYINT(1)   DEFAULT 0,
    lemas_malaise    TINYINT(1)   DEFAULT 0,
    hasil            ENUM('campak','rubella','cacar') NOT NULL,
    confidence       FLOAT        NOT NULL,
    prob_campak      FLOAT        DEFAULT NULL,
    prob_rubella     FLOAT        DEFAULT NULL,
    prob_cacar       FLOAT        DEFAULT NULL,
    status           ENUM('selesai','review','dihapus') DEFAULT 'selesai',
    triple_data      TEXT         DEFAULT NULL,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES model_versions(id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- DATA AWAL
-- Password admin: admin123
-- ─────────────────────────────────────────────
INSERT INTO users (nama, email, password, role) VALUES
('Administrator', 'admin@dermdetect.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBpj2/tCJfLPi2', 'admin');

INSERT INTO model_versions (versi, nama_file, akurasi, f1_score, keterangan, is_active, uploaded_by)
VALUES ('v1.0', 'best_model.keras', 0.9317, 0.93,
        'Model awal MobileNetV2 + MLP, training phase 1 & 2', 1, 1);
