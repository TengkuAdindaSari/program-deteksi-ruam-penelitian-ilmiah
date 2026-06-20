<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();

$user  = getUser();
$token = getToken();
$id    = (int)($_GET['id'] ?? 0);

$res = Api::get("/diagnose/history/$id", $token);
$d   = $res['data'] ?? null;

if (!$d) {
    flash('danger', 'Data diagnosis tidak ditemukan.');
    header('Location: /user/history.php');
    exit;
}

// Ambil triple result dari database, fallback ke session jika tidak ada
$triple = $d['triple'] ?? null;
if (!$triple) {
    $tripleKey = 'triple_result_' . $id;
    $triple    = $_SESSION[$tripleKey] ?? null;
    unset($_SESSION[$tripleKey]);
}

$infoMap = [
    'campak'  => [
        'label'     => 'Campak',
        'icon'      => '🔴',
        'class'     => 'campak',
        'badge'     => 'badge-blue',
        'color'     => '#2563EB',
        'gejala'    => ['Demam tinggi 38-40°C', 'Batuk kering', 'Mata merah (konjungtivitis)', 'Ruam merah menyebar dari wajah ke badan', 'Bercak Koplik di mulut'],
        'penanganan'=> 'Istirahat dan cukup cairan. Konsultasikan ke dokter. Vaksin MMR untuk pencegahan.',
    ],
    'rubella' => [
        'label'     => 'Rubella',
        'icon'      => '🟠',
        'class'     => 'rubella',
        'badge'     => 'badge-amber',
        'color'     => '#F59E0B',
        'gejala'    => ['Demam ringan 2-3 hari', 'Ruam merah muda menyebar cepat', 'Pembengkakan kelenjar getah bening', 'Nyeri sendi (dewasa)'],
        'penanganan'=> 'Istirahat dan cukup cairan. Vaksin MMR. Ibu hamil segera ke dokter.',
    ],
    'cacar'   => [
        'label'     => 'Cacar Air',
        'icon'      => '🟡',
        'class'     => 'cacar',
        'badge'     => 'badge-green',
        'color'     => '#10B981',
        'gejala'    => ['Demam ringan-sedang', 'Ruam berupa vesikel berisi cairan', 'Sangat gatal', 'Ruam muncul bertahap dari kepala ke badan'],
        'penanganan'=> 'Jaga kebersihan, jangan digaruk. Obat anti-gatal sesuai dokter. Vaksin Varisela.',
    ],
];

$info = $infoMap[$d['hasil']] ?? $infoMap['campak'];
$prob = $d['probabilitas'];

// Warna indikator konsistensi
$konsistensiColor = [
    'konsisten'       => ['bg' => '#ECFDF5', 'border' => '#A7F3D0', 'text' => '#065F46', 'icon' => 'ti-circle-check'],
    'mayoritas'       => ['bg' => '#FFFBEB', 'border' => '#FDE68A', 'text' => '#92400E', 'icon' => 'ti-alert-triangle'],
    'tidak_konsisten' => ['bg' => '#FEF2F2', 'border' => '#FECACA', 'text' => '#991B1B', 'icon' => 'ti-circle-x'],
];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hasil Diagnosis — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
        /* ── Triple Result Cards ── */
        .triple-card {
            background: var(--white);
            border: 1px solid var(--gray-200);
            border-radius: var(--radius-lg);
            overflow: hidden;
            margin-bottom: 12px;
        }
        .triple-header {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--gray-100);
        }
        .triple-header .method-badge {
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 99px;
            margin-left: auto;
        }
        .triple-body { padding: 14px 16px; }

        /* ── Result Pill ── */
        .result-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 99px;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        /* ── Mini Probability Bars ── */
        .mini-prob  { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
        .mini-label { font-size: 11px; color: var(--gray-500); width: 70px; }
        .mini-track { flex: 1; height: 6px; background: var(--gray-100); border-radius: 99px; overflow: hidden; }
        .mini-fill  { height: 100%; border-radius: 99px; }
        .mini-pct   { font-size: 11px; font-weight: 500; color: var(--gray-700); width: 38px; text-align: right; }

        /* ── Fusion Banner ── */
        .fusion-banner {
            background: linear-gradient(135deg, #EFF6FF, #F0FDF4);
            border: 2px solid #2563EB;
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 16px;
            text-align: center;
        }
        .fusion-title   { font-size: 12px; font-weight: 600; color: #2563EB; margin-bottom: 8px; letter-spacing: .05em; text-transform: uppercase; }
        .fusion-disease { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
        .fusion-conf    { font-size: 14px; color: var(--gray-600); }

        /* ── Konsistensi Box ── */
        .konsistensi-box {
            border-radius: var(--radius);
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            font-size: 13px;
            font-weight: 500;
        }

        /* ── Comparison Table ── */
        .comparison-row {
            display: grid;
            grid-template-columns: 110px 1fr 1fr 1fr;
            gap: 8px;
            padding: 8px 0;
            border-bottom: 1px solid var(--gray-100);
            align-items: center;
            font-size: 12px;
        }
        .comparison-row:last-child { border-bottom: none; }
        .comparison-header {
            background: var(--gray-50);
            border-radius: var(--radius);
            font-weight: 600;
            color: var(--gray-600);
            padding: 8px !important;
        }
    </style>
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
        <h2 class="page-title" style="margin:0;">Hasil Diagnosis Lengkap</h2>
        <span class="text-sm text-muted ml-auto">
            <?= date('d M Y, H:i', strtotime($d['created_at'])) ?>
        </span>
    </div>

    <?php if ($triple): ?>

    <!-- ════════ HASIL UTAMA (FUSION) ════════ -->
    <div class="fusion-banner">
        <div class="fusion-title">🔀 Hasil Diagnosis Utama (Gabungan Foto + Gejala)</div>
        <div class="fusion-disease" style="color:<?= $info['color'] ?>;">
            <?= $info['icon'] ?> <?= $info['label'] ?>
        </div>
        <div class="fusion-conf">Keyakinan: <strong><?= $triple['fusion']['confidence'] ?>%</strong></div>
    </div>

    <!-- ════════ INDIKATOR KONSISTENSI ════════ -->
    <?php
    $kStatus = $triple['konsistensi']['status'] ?? 'mayoritas';
    $kStyle  = $konsistensiColor[$kStatus] ?? $konsistensiColor['mayoritas'];
    ?>
    <div class="konsistensi-box" style="background:<?= $kStyle['bg'] ?>;border:1px solid <?= $kStyle['border'] ?>;color:<?= $kStyle['text'] ?>;">
        <i class="ti <?= $kStyle['icon'] ?>" style="font-size:20px;flex-shrink:0;"></i>
        <div>
            <div style="font-weight:700;"><?= htmlspecialchars($triple['konsistensi']['label']) ?></div>
            <div style="font-size:12px;font-weight:400;margin-top:2px;">
                <?php if ($kStatus === 'konsisten'): ?>
                Ketiga metode analisis menghasilkan kesimpulan yang sama. Tingkat kepercayaan tinggi.
                <?php elseif ($kStatus === 'mayoritas'): ?>
                Dua dari tiga metode sepakat. Disarankan tetap konsultasi dengan dokter.
                <?php else: ?>
                Ketiga metode menghasilkan kesimpulan berbeda. Wajib konsultasi dokter untuk kepastian.
                <?php endif; ?>
            </div>
        </div>
    </div>

    <div class="grid-2">
        <!-- ════════ KIRI: Triple Result ════════ -->
        <div>

            <!-- Tabel Perbandingan -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-table" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Perbandingan Hasil Analisis</h3>
                </div>
                <div class="card-body" style="padding:12px 16px;">
                    <!-- Header -->
                    <div class="comparison-row comparison-header">
                        <div>Metode</div>
                        <div style="text-align:center;">Campak</div>
                        <div style="text-align:center;">Rubella</div>
                        <div style="text-align:center;">Cacar Air</div>
                    </div>
                    <?php
                    $methods = [
                        ['key' => 'cnn',    'label' => '📸 Visual (CNN)'],
                        ['key' => 'mlp',    'label' => '🩺 Gejala (MLP)'],
                        ['key' => 'fusion', 'label' => '🔀 Gabungan'],
                    ];
                    foreach ($methods as $m):
                        $r    = $triple[$m['key']];
                        $pred = $r['probabilitas'];
                    ?>
                    <div class="comparison-row">
                        <div style="font-weight:500;"><?= $m['label'] ?></div>
                        <?php foreach (['campak' => '#2563EB', 'rubella' => '#F59E0B', 'cacar' => '#10B981'] as $cls => $col):
                            $pct    = $pred[$cls];
                            $isBest = ($r['prediksi'] === $cls);
                        ?>
                        <div style="text-align:center;">
                            <span style="font-weight:<?= $isBest ? '700' : '400' ?>;color:<?= $isBest ? $col : '#6B7280' ?>;">
                                <?= $pct ?>%
                                <?php if ($isBest): ?>
                                <i class="ti ti-arrow-badge-up" style="font-size:11px;"></i>
                                <?php endif; ?>
                            </span>
                        </div>
                        <?php endforeach; ?>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>

            <!-- Card CNN Only -->
            <div class="triple-card">
                <div class="triple-header">
                    <i class="ti ti-camera" style="color:#7C3AED;font-size:18px;"></i>
                    <div>
                        <div style="font-weight:600;font-size:13px;">Analisis Visual (CNN Only)</div>
                        <div class="text-sm text-muted">Berdasarkan foto saja, tanpa gejala</div>
                    </div>
                    <span class="method-badge" style="background:#F5F3FF;color:#7C3AED;">📸 Foto</span>
                </div>
                <div class="triple-body">
                    <?php
                    $cnn     = $triple['cnn'];
                    $cnnInfo = $infoMap[$cnn['prediksi']] ?? $infoMap['campak'];
                    ?>
                    <div class="result-pill" style="background:<?= $cnnInfo['color'] ?>22;color:<?= $cnnInfo['color'] ?>;">
                        <?= $cnnInfo['icon'] ?> <?= $cnnInfo['label'] ?>
                        <span style="font-size:13px;font-weight:500;"><?= $cnn['confidence'] ?>%</span>
                    </div>
                    <?php foreach (['campak' => '#2563EB', 'rubella' => '#F59E0B', 'cacar' => '#10B981'] as $cls => $col): ?>
                    <div class="mini-prob">
                        <div class="mini-label"><?= $cls === 'cacar' ? 'Cacar Air' : ucfirst($cls) ?></div>
                        <div class="mini-track">
                            <div class="mini-fill" style="width:<?= $cnn['probabilitas'][$cls] ?>%;background:<?= $col ?>;"></div>
                        </div>
                        <div class="mini-pct"><?= $cnn['probabilitas'][$cls] ?>%</div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>

            <!-- Card MLP Only -->
            <div class="triple-card">
                <div class="triple-header">
                    <i class="ti ti-clipboard-list" style="color:#059669;font-size:18px;"></i>
                    <div>
                        <div style="font-weight:600;font-size:13px;">Analisis Gejala (MLP Only)</div>
                        <div class="text-sm text-muted">Berdasarkan gejala saja, tanpa foto</div>
                    </div>
                    <span class="method-badge" style="background:#ECFDF5;color:#059669;">🩺 Gejala</span>
                </div>
                <div class="triple-body">
                    <?php
                    $mlp     = $triple['mlp'];
                    $mlpInfo = $infoMap[$mlp['prediksi']] ?? $infoMap['campak'];
                    ?>
                    <div class="result-pill" style="background:<?= $mlpInfo['color'] ?>22;color:<?= $mlpInfo['color'] ?>;">
                        <?= $mlpInfo['icon'] ?> <?= $mlpInfo['label'] ?>
                        <span style="font-size:13px;font-weight:500;"><?= $mlp['confidence'] ?>%</span>
                    </div>
                    <?php foreach (['campak' => '#2563EB', 'rubella' => '#F59E0B', 'cacar' => '#10B981'] as $cls => $col): ?>
                    <div class="mini-prob">
                        <div class="mini-label"><?= $cls === 'cacar' ? 'Cacar Air' : ucfirst($cls) ?></div>
                        <div class="mini-track">
                            <div class="mini-fill" style="width:<?= $mlp['probabilitas'][$cls] ?>%;background:<?= $col ?>;"></div>
                        </div>
                        <div class="mini-pct"><?= $mlp['probabilitas'][$cls] ?>%</div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>

        <!-- ════════ KANAN: Info Penyakit & Gejala ════════ -->
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
                    <div class="flex gap-2" style="padding:3px 0;">
                        <i class="ti ti-circle-dot" style="color:<?= $info['color'] ?>;flex-shrink:0;margin-top:2px;"></i>
                        <span class="text-sm"><?= $g ?></span>
                    </div>
                    <?php endforeach; ?>
                    <hr class="divider">
                    <div style="font-weight:600;font-size:13px;margin-bottom:8px;">Penanganan</div>
                    <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:12px;font-size:13px;color:#065F46;">
                        <i class="ti ti-heart-handshake"></i> <?= $info['penanganan'] ?>
                    </div>
                </div>
            </div>

            <!-- Gejala yang Diinput -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-clipboard-check" style="color:#10B981;font-size:18px;"></i>
                    <h3>Gejala yang Diinput</h3>
                </div>
                <div class="card-body">
                    <?php
                    $g     = $d['gejala'];
                    $items = [
                        'Durasi demam'               => $g['durasi_demam'] . ' hari',
                        'Demam tinggi (>38.5°C)'     => ($g['demam_tinggi'] ?? 0) ? 'Ya' : 'Tidak',
                        'Batuk kering'               => ($g['batuk'] ?? 0) ? 'Ya' : 'Tidak',
                        'Pilek / hidung tersumbat'   => ($g['pilek'] ?? 0) ? 'Ya' : 'Tidak',
                        'Sakit tenggorokan'          => ($g['sakit_tenggorokan'] ?? 0) ? 'Ya' : 'Tidak',
                        'Mata merah'                 => ($g['mata_merah'] ?? 0) ? 'Ya' : 'Tidak',
                        'Bercak koplik di mulut'     => ($g['koplik_spot'] ?? 0) ? 'Ya' : 'Tidak',
                        'Kelenjar bengkak'           => ($g['kelenjar_bengkak'] ?? 0) ? 'Ya' : 'Tidak',
                        'Ruam wajah ke badan'        => ($g['pola_ruam'] ?? 0) ? 'Ya' : 'Tidak',
                        'Nyeri sendi'                => ($g['nyeri_sendi'] ?? 0) ? 'Ya' : 'Tidak',
                        'Vesikel (gelembung cairan)' => ($g['vesikel'] ?? 0) ? 'Ya' : 'Tidak',
                        'Hilang nafsu makan'         => ($g['hilang_nafsu_makan'] ?? 0) ? 'Ya' : 'Tidak',
                        'Badan lemas & cepat lelah'  => ($g['lemas'] ?? 0) ? 'Ya' : 'Tidak',
                    ];
                    foreach ($items as $label => $val):
                    ?>
                    <div class="flex items-center" style="padding:6px 0;border-bottom:1px solid #F3F4F6;">
                        <span class="text-muted text-sm" style="width:190px;"><?= $label ?></span>
                        <span style="font-weight:500;color:<?= ($val === 'Ya') ? '#10B981' : '#6B7280' ?>;">
                            <?= $val ?>
                        </span>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>

            <!-- Disclaimer & Aksi -->
            <div class="card">
                <div class="card-body">
                    <div class="disclaimer mb-3">
                        <i class="ti ti-alert-triangle"></i>
                        Hasil ini hanya referensi awal berbasis AI. Selalu konsultasikan dengan dokter atau tenaga medis profesional untuk diagnosis dan penanganan yang tepat.
                    </div>
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

    <?php else: ?>
    <!-- ════════ FALLBACK: data dari riwayat lama (tanpa triple) ════════ -->
    <div class="grid-2">
        <div>
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-report-medical" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Hasil Prediksi</h3>
                </div>
                <div class="card-body">
                    <div class="result-box <?= $info['class'] ?>">
                        <div class="result-disease"><?= $info['icon'] ?> <?= $info['label'] ?></div>
                        <div class="result-conf">Keyakinan: <strong><?= $d['confidence'] ?>%</strong></div>
                    </div>
                    <div style="font-weight:600;font-size:13px;margin-bottom:10px;">Probabilitas per Kelas</div>
                    <?php foreach (['campak' => ['Campak', '#2563EB'], 'rubella' => ['Rubella', '#F59E0B'], 'cacar' => ['Cacar Air', '#10B981']] as $cls => [$lbl, $col]): ?>
                    <div class="progress-row">
                        <div class="progress-label"><?= $lbl ?></div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width:<?= $prob[$cls] ?>%;background:<?= $col ?>;"></div>
                        </div>
                        <div class="progress-pct"><?= $prob[$cls] ?>%</div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>

            <!-- Gejala yang Diinput -->
            <div class="card">
                <div class="card-header">
                    <i class="ti ti-clipboard-list" style="color:#10B981;font-size:18px;"></i>
                    <h3>Gejala yang Diinput</h3>
                </div>
                <div class="card-body">
                    <?php
                    $g     = $d['gejala'];
                    $items = [
                        'Durasi demam'               => $g['durasi_demam'] . ' hari',
                        'Demam tinggi (>38.5°C)'     => ($g['demam_tinggi'] ?? 0) ? 'Ya' : 'Tidak',
                        'Batuk kering'               => ($g['batuk'] ?? 0) ? 'Ya' : 'Tidak',
                        'Pilek / hidung tersumbat'   => ($g['pilek'] ?? 0) ? 'Ya' : 'Tidak',
                        'Sakit tenggorokan'          => ($g['sakit_tenggorokan'] ?? 0) ? 'Ya' : 'Tidak',
                        'Mata merah'                 => ($g['mata_merah'] ?? 0) ? 'Ya' : 'Tidak',
                        'Bercak koplik di mulut'     => ($g['koplik_spot'] ?? 0) ? 'Ya' : 'Tidak',
                        'Kelenjar bengkak'           => ($g['kelenjar_bengkak'] ?? 0) ? 'Ya' : 'Tidak',
                        'Ruam wajah ke badan'        => ($g['pola_ruam'] ?? 0) ? 'Ya' : 'Tidak',
                        'Nyeri sendi'                => ($g['nyeri_sendi'] ?? 0) ? 'Ya' : 'Tidak',
                        'Vesikel (gelembung cairan)' => ($g['vesikel'] ?? 0) ? 'Ya' : 'Tidak',
                        'Hilang nafsu makan'         => ($g['hilang_nafsu_makan'] ?? 0) ? 'Ya' : 'Tidak',
                        'Badan lemas & cepat lelah'  => ($g['lemas'] ?? 0) ? 'Ya' : 'Tidak',
                    ];
                    foreach ($items as $label => $val):
                    ?>
                    <div class="flex items-center" style="padding:7px 0;border-bottom:1px solid #F3F4F6;">
                        <span class="text-muted text-sm" style="width:190px;"><?= $label ?></span>
                        <span style="font-weight:500;color:<?= ($val === 'Ya') ? '#10B981' : '#6B7280' ?>;">
                            <?= $val ?>
                        </span>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>

        <div>
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
                        <i class="ti ti-circle-dot" style="color:<?= $info['color'] ?>;flex-shrink:0;margin-top:2px;"></i>
                        <span class="text-sm"><?= $g ?></span>
                    </div>
                    <?php endforeach; ?>
                    <hr class="divider">
                    <div style="font-weight:600;font-size:13px;margin-bottom:8px;">Penanganan</div>
                    <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:12px;font-size:13px;color:#065F46;">
                        <i class="ti ti-heart-handshake"></i> <?= $info['penanganan'] ?>
                    </div>
                    <div class="disclaimer mt-3">
                        <i class="ti ti-alert-triangle"></i>
                        Hasil ini hanya referensi awal. Konsultasikan ke dokter.
                    </div>
                </div>
            </div>

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
    <?php endif; ?>
</div>

</body>
</html>
