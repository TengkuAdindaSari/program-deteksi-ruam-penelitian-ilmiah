<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();

$user  = getUser();
$token = getToken();
$id    = (int)($_GET['id'] ?? 0);

$res  = Api::get("/diagnose/history/$id", $token);
$d    = $res['data'] ?? null;

if (!$d) {
    flash('danger', 'Data diagnosis tidak ditemukan.');
    header('Location: /user/history.php');
    exit;
}

$infoMap = [
    'campak'  => [
        'label'     => 'Campak',
        'icon'      => '🔴',
        'class'     => 'campak',
        'badge'     => 'badge-blue',
        'gejala'    => ['Demam tinggi 38-40°C', 'Batuk kering', 'Mata merah (konjungtivitis)', 'Ruam merah menyebar dari wajah ke badan', 'Bercak Koplik di mulut'],
        'penanganan'=> 'Istirahat dan cukup cairan. Konsultasikan ke dokter. Vaksin MMR untuk pencegahan.',
    ],
    'rubella' => [
        'label'     => 'Rubella',
        'icon'      => '🟠',
        'class'     => 'rubella',
        'badge'     => 'badge-amber',
        'gejala'    => ['Demam ringan 2-3 hari', 'Ruam merah muda menyebar cepat', 'Pembengkakan kelenjar getah bening', 'Nyeri sendi (dewasa)'],
        'penanganan'=> 'Istirahat dan cukup cairan. Vaksin MMR. Ibu hamil segera ke dokter.',
    ],
    'cacar'   => [
        'label'     => 'Cacar Air',
        'icon'      => '🟡',
        'class'     => 'cacar',
        'badge'     => 'badge-green',
        'gejala'    => ['Demam ringan-sedang', 'Ruam berupa vesikel berisi cairan', 'Sangat gatal', 'Ruam muncul bertahap dari kepala ke badan'],
        'penanganan'=> 'Jaga kebersihan, jangan digaruk. Obat anti-gatal sesuai dokter. Vaksin Varisela.',
    ],
];

$info  = $infoMap[$d['hasil']] ?? $infoMap['campak'];
$prob  = $d['probabilitas'];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hasil Diagnosis — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<nav class="navbar">
    <div class="navbar-brand"><i class="ti ti-stethoscope"></i> DermDetect</div>
    <div class="navbar-links">
        <a href="/user/dashboard.php" class="nav-link">Dashboard</a>
        <a href="/user/diagnose.php" class="nav-link">Diagnosis</a>
        <a href="/user/history.php" class="nav-link active">Riwayat</a>
        <a href="/user/profile.php" class="nav-link">Profil</a>
    </div>
    <div class="nav-avatar"><?= strtoupper(substr($user['nama'], 0, 2)) ?></div>
    <a href="/logout.php" class="btn btn-secondary btn-sm" style="margin-left:8px;">
        <i class="ti ti-logout"></i> Keluar
    </a>
</nav>

<div class="container">
    <div class="flex items-center gap-2 mb-4">
        <a href="/user/history.php" class="btn btn-secondary btn-sm">
            <i class="ti ti-arrow-left"></i> Kembali
        </a>
        <h2 class="page-title" style="margin:0;">Hasil Diagnosis</h2>
        <span class="text-sm text-muted ml-auto">
            <?= date('d M Y, H:i', strtotime($d['created_at'])) ?>
        </span>
    </div>

    <div class="grid-2">
        <!-- Kiri -->
        <div>
            <!-- Hasil Prediksi -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-report-medical" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Hasil Prediksi</h3>
                </div>
                <div class="card-body">
                    <div class="result-box <?= $info['class'] ?>">
                        <div class="result-disease">
                            <?= $info['icon'] ?> <?= $info['label'] ?>
                        </div>
                        <div class="result-conf">
                            Keyakinan model: <strong><?= $d['confidence'] ?>%</strong>
                        </div>
                    </div>

                    <div style="font-weight:600;font-size:13px;margin-bottom:10px;">Probabilitas per Kelas</div>
                    <div class="progress-row">
                        <div class="progress-label">Campak</div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width:<?= $prob['campak'] ?>%;background:#2563EB;"></div>
                        </div>
                        <div class="progress-pct"><?= $prob['campak'] ?>%</div>
                    </div>
                    <div class="progress-row">
                        <div class="progress-label">Rubella</div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width:<?= $prob['rubella'] ?>%;background:#F59E0B;"></div>
                        </div>
                        <div class="progress-pct"><?= $prob['rubella'] ?>%</div>
                    </div>
                    <div class="progress-row">
                        <div class="progress-label">Cacar Air</div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width:<?= $prob['cacar'] ?>%;background:#10B981;"></div>
                        </div>
                        <div class="progress-pct"><?= $prob['cacar'] ?>%</div>
                    </div>
                </div>
            </div>

            <!-- Gejala yang diinput -->
            <div class="card">
                <div class="card-header">
                    <i class="ti ti-clipboard-list" style="color:#10B981;font-size:18px;"></i>
                    <h3>Gejala yang Diinput</h3>
                </div>
                <div class="card-body">
                    <?php
                    $g = $d['gejala'];
                    $items = [
                        'Durasi demam'             => $g['durasi_demam'] . ' hari',
                        'Batuk'                    => $g['batuk'] ? 'Ya' : 'Tidak',
                        'Mata merah'               => $g['mata_merah'] ? 'Ya' : 'Tidak',
                        'Kelenjar bengkak'         => $g['kelenjar_bengkak'] ? 'Ya' : 'Tidak',
                        'Ruam wajah ke badan'      => $g['pola_ruam'] ? 'Ya' : 'Tidak',
                        'Vesikel (gelembung cairan)' => $g['vesikel'] ? 'Ya' : 'Tidak',
                    ];
                    foreach ($items as $label => $val):
                    ?>
                    <div class="flex items-center" style="padding:7px 0;border-bottom:1px solid #F3F4F6;">
                        <span class="text-muted" style="width:180px;"><?= $label ?></span>
                        <span style="font-weight:500;color:<?= ($val === 'Ya') ? '#10B981' : ($val === 'Tidak' ? '#6B7280' : '#1F2937') ?>;">
                            <?= $val ?>
                        </span>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>

        <!-- Kanan -->
        <div>
            <!-- Info Penyakit -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-info-circle" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Informasi Penyakit</h3>
                    <span class="badge <?= $info['badge'] ?> ml-auto"><?= $info['label'] ?></span>
                </div>
                <div class="card-body">
                    <div style="font-weight:600;font-size:13px;margin-bottom:8px;">Gejala Umum</div>
                    <?php foreach ($info['gejala'] as $g): ?>
                    <div class="flex gap-2" style="padding:4px 0;">
                        <i class="ti ti-circle-dot" style="color:#2563EB;flex-shrink:0;margin-top:2px;"></i>
                        <span class="text-sm"><?= $g ?></span>
                    </div>
                    <?php endforeach; ?>

                    <hr class="divider">

                    <div style="font-weight:600;font-size:13px;margin-bottom:8px;">Penanganan</div>
                    <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:12px;font-size:13px;color:#065F46;">
                        <i class="ti ti-heart-handshake"></i>
                        <?= $info['penanganan'] ?>
                    </div>

                    <div class="disclaimer">
                        <i class="ti ti-alert-triangle"></i>
                        Hasil ini hanya referensi awal. Konsultasikan dengan dokter untuk diagnosis dan penanganan yang tepat.
                    </div>
                </div>
            </div>

            <!-- Aksi -->
            <div class="card">
                <div class="card-body">
                    <a href="/user/diagnose.php" class="btn btn-primary btn-block mb-2">
                        <i class="ti ti-plus"></i> Diagnosis Baru
                    </a>
                    <a href="/user/history.php" class="btn btn-secondary btn-block">
                        <i class="ti ti-history"></i> Lihat Semua Riwayat
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
