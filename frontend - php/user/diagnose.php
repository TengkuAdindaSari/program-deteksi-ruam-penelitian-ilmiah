<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
if (isAdmin()) { header('Location: /admin/dashboard.php'); exit; }

$user  = getUser();
$token = getToken();
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (empty($_FILES['foto']['tmp_name'])) {
        $error = 'Foto wajib diupload';
    } else {
        $data = [
            'durasi_demam'     => (int)($_POST['durasi_demam'] ?? 4),
            'batuk'            => isset($_POST['batuk'])            ? 1 : 0,
            'mata_merah'       => isset($_POST['mata_merah'])       ? 1 : 0,
            'kelenjar_bengkak' => isset($_POST['kelenjar_bengkak']) ? 1 : 0,
            'pola_ruam'        => isset($_POST['pola_ruam'])        ? 1 : 0,
            'vesikel'          => isset($_POST['vesikel'])          ? 1 : 0,
        ];

        $res = Api::post('/diagnose/predict', $data, $token, ['foto' => $_FILES['foto']]);

        if ($res['success'] ?? false) {
            $id = $res['data']['id'];
            // Simpan triple result ke session untuk ditampilkan di halaman result
            $_SESSION['triple_result_' . $id] = $res['data']['triple'] ?? null;
            header("Location: /user/result.php?id=$id");
            exit;
        } else {
            $error = $res['message'] ?? 'Prediksi gagal, coba lagi';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnosis — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<nav class="navbar">
    <div class="navbar-brand"><i class="ti ti-stethoscope"></i> DermDetect</div>
    <div class="navbar-links">
        <a href="/user/dashboard.php" class="nav-link">Dashboard</a>
        <a href="/user/diagnose.php" class="nav-link active">Diagnosis</a>
        <a href="/user/history.php" class="nav-link">Riwayat</a>
        <a href="/user/profile.php" class="nav-link">Profil</a>
    </div>
    <div class="nav-avatar"><?= strtoupper(substr($user['nama'], 0, 2)) ?></div>
    <a href="/logout.php" class="btn btn-secondary btn-sm" style="margin-left:8px;">
        <i class="ti ti-logout"></i> Keluar
    </a>
</nav>

<div class="container">
    <h2 class="page-title">Diagnosis Penyakit Ruam Kulit</h2>

    <!-- Step indicator -->
    <div class="flex items-center gap-2 mb-4" style="font-size:13px;">
        <span style="background:#2563EB;color:#fff;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">1</span>
        <span style="font-weight:500;color:#2563EB;">Upload Foto</span>
        <span style="flex:1;height:1px;background:#E5E7EB;"></span>
        <span style="background:#E5E7EB;color:#6B7280;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">2</span>
        <span style="color:#6B7280;">Isi Gejala</span>
        <span style="flex:1;height:1px;background:#E5E7EB;"></span>
        <span style="background:#E5E7EB;color:#6B7280;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">3</span>
        <span style="color:#6B7280;">Hasil</span>
    </div>

    <?php if ($error): ?>
    <div class="alert alert-danger"><i class="ti ti-alert-circle"></i> <?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <form method="POST" enctype="multipart/form-data">
        <div class="grid-2">
            <!-- Kiri: Upload + Gejala -->
            <div>
                <div class="card mb-4">
                    <div class="card-header">
                        <i class="ti ti-photo" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Upload Foto Ruam Kulit</h3>
                    </div>
                    <div class="card-body">
                        <div class="upload-box" onclick="document.getElementById('fotoInput').click();">
                            <i class="ti ti-cloud-upload"></i>
                            <p><strong>Klik untuk pilih foto</strong><br>atau drag &amp; drop di sini</p>
                            <p class="text-sm text-muted mt-1">JPG, PNG — maks. 5MB</p>
                        </div>
                        <input type="file" id="fotoInput" name="foto" accept="image/*"
                               style="display:none;" onchange="previewFoto(this)" required>
                        <img id="previewImg" class="upload-preview" src="" alt="Preview">
                        <p id="namaFile" class="text-sm text-muted mt-1"></p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-clipboard-list" style="color:#10B981;font-size:18px;"></i>
                        <h3>Gejala Klinis</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">
                                Durasi demam: <strong id="durasiVal">4</strong> hari
                            </label>
                            <input type="range" name="durasi_demam" min="0" max="14" value="4"
                                   oninput="document.getElementById('durasiVal').textContent=this.value">
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="batuk" name="batuk">
                            <label for="batuk">Batuk kering</label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="mata_merah" name="mata_merah">
                            <label for="mata_merah">Mata merah (konjungtivitis)</label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="kelenjar_bengkak" name="kelenjar_bengkak">
                            <label for="kelenjar_bengkak">Pembengkakan kelenjar getah bening</label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="pola_ruam" name="pola_ruam">
                            <label for="pola_ruam">Ruam menyebar dari wajah ke badan</label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="vesikel" name="vesikel">
                            <label for="vesikel">Ruam berupa gelembung berisi cairan</label>
                        </div>

                        <button type="submit" class="btn btn-primary btn-block mt-4">
                            <i class="ti ti-brain"></i> Analisis Sekarang
                        </button>
                    </div>
                </div>
            </div>

            <!-- Kanan: Info -->
            <div>
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-info-circle" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Panduan Penggunaan</h3>
                    </div>
                    <div class="card-body">
                        <div style="display:flex;flex-direction:column;gap:16px;">
                            <div class="flex gap-3">
                                <div style="width:32px;height:32px;background:#EFF6FF;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                                    <i class="ti ti-camera" style="color:#2563EB;"></i>
                                </div>
                                <div>
                                    <div style="font-weight:600;font-size:13px;margin-bottom:2px;">Tips Foto yang Baik</div>
                                    <div class="text-sm text-muted">Ambil foto dengan pencahayaan yang cukup. Pastikan ruam terlihat jelas dan fokus. Hindari bayangan atau blur.</div>
                                </div>
                            </div>
                            <div class="flex gap-3">
                                <div style="width:32px;height:32px;background:#ECFDF5;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                                    <i class="ti ti-clipboard-check" style="color:#10B981;"></i>
                                </div>
                                <div>
                                    <div style="font-weight:600;font-size:13px;margin-bottom:2px;">Isi Gejala dengan Jujur</div>
                                    <div class="text-sm text-muted">Centang gejala yang benar-benar dialami. Data gejala membantu meningkatkan akurasi prediksi model.</div>
                                </div>
                            </div>
                            <div class="flex gap-3">
                                <div style="width:32px;height:32px;background:#FFFBEB;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                                    <i class="ti ti-stethoscope" style="color:#F59E0B;"></i>
                                </div>
                                <div>
                                    <div style="font-weight:600;font-size:13px;margin-bottom:2px;">Penyakit yang Dideteksi</div>
                                    <div class="text-sm text-muted">
                                        <span class="badge badge-blue" style="margin-right:4px;">Campak</span>
                                        <span class="badge badge-amber" style="margin-right:4px;">Rubella</span>
                                        <span class="badge badge-green">Cacar Air</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="disclaimer mt-4">
                            <i class="ti ti-alert-triangle"></i>
                            Hasil diagnosis ini hanya sebagai referensi awal berbasis AI.
                            Selalu konsultasikan dengan dokter atau tenaga medis profesional
                            untuk diagnosis dan penanganan yang tepat.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<script>
function previewFoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            const img = document.getElementById('previewImg');
            img.src = e.target.result;
            img.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
        document.getElementById('namaFile').textContent = input.files[0].name;
    }
}
</script>
</body>
</html>
