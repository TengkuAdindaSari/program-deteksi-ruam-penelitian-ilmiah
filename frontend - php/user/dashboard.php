<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
if (isAdmin()) { header('Location: /admin/dashboard.php'); exit; }

$user  = getUser();
$token = getToken();
$res   = Api::get('/user/dashboard', $token);
$data  = $res['data'] ?? [];
$stat  = $data['statistik'] ?? [];
$riwayat = $data['riwayat_terbaru'] ?? [];

$flash = getFlash();
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<!-- Navbar -->
<nav class="navbar">
    <div class="navbar-brand">
        <i class="ti ti-stethoscope"></i> DermDetect
    </div>
    <div class="navbar-links">
        <a href="/user/dashboard.php" class="nav-link active">Dashboard</a>
        <a href="/user/diagnose.php" class="nav-link">Diagnosis</a>
        <a href="/user/history.php" class="nav-link">Riwayat</a>
        <a href="/user/profile.php" class="nav-link">Profil</a>
    </div>
    <div class="nav-avatar"><?= strtoupper(substr($user['nama'], 0, 2)) ?></div>
    <a href="/logout.php" class="btn btn-secondary btn-sm" style="margin-left:8px;">
        <i class="ti ti-logout"></i> Keluar
    </a>
</nav>

<div class="container">
    <?php if ($flash): ?>
    <div class="alert alert-<?= $flash['type'] === 'success' ? 'success' : 'danger' ?>">
        <i class="ti ti-<?= $flash['type'] === 'success' ? 'check' : 'alert-circle' ?>"></i>
        <?= htmlspecialchars($flash['message']) ?>
    </div>
    <?php endif; ?>

    <h2 class="page-title">Selamat datang, <?= htmlspecialchars($user['nama']) ?>!</h2>

    <!-- Metrik -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Diagnosis</div>
            <div class="metric-value"><?= $stat['total'] ?? 0 ?></div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Campak</div>
            <div class="metric-value" style="color:#2563EB;"><?= $stat['campak'] ?? 0 ?></div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Rubella</div>
            <div class="metric-value" style="color:#F59E0B;"><?= $stat['rubella'] ?? 0 ?></div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Cacar Air</div>
            <div class="metric-value" style="color:#10B981;"><?= $stat['cacar'] ?? 0 ?></div>
        </div>
    </div>

    <div class="grid-2">
        <!-- Mulai Diagnosis -->
        <div class="card">
            <div class="card-header">
                <i class="ti ti-plus-health" style="color:#2563EB;font-size:18px;"></i>
                <h3>Mulai Diagnosis Baru</h3>
            </div>
            <div class="card-body" style="text-align:center; padding:32px;">
                <i class="ti ti-camera-selfie" style="font-size:48px;color:#2563EB;display:block;margin-bottom:16px;"></i>
                <p class="text-muted mb-3">Upload foto ruam kulit dan isi gejala klinis untuk mendapatkan prediksi penyakit.</p>
                <a href="/user/diagnose.php" class="btn btn-primary">
                    <i class="ti ti-upload"></i> Mulai Diagnosis
                </a>
            </div>
        </div>

        <!-- Riwayat Terbaru -->
        <div class="card">
            <div class="card-header">
                <i class="ti ti-history" style="color:#2563EB;font-size:18px;"></i>
                <h3>Riwayat Terbaru</h3>
                <a href="/user/history.php" class="btn btn-secondary btn-sm ml-auto">Lihat semua</a>
            </div>
            <?php if (empty($riwayat)): ?>
            <div class="card-body" style="text-align:center;padding:32px;">
                <i class="ti ti-file-off" style="font-size:32px;color:#9CA3AF;"></i>
                <p class="text-muted mt-2">Belum ada riwayat diagnosis.</p>
            </div>
            <?php else: ?>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Tanggal</th>
                            <th>Hasil</th>
                            <th>Keyakinan</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($riwayat as $d): ?>
                        <tr>
                            <td><?= date('d M Y', strtotime($d['created_at'])) ?></td>
                            <td>
                                <?php
                                $badgeClass = ['campak'=>'badge-blue','rubella'=>'badge-amber','cacar'=>'badge-green'][$d['hasil']] ?? 'badge-gray';
                                $label = ['campak'=>'Campak','rubella'=>'Rubella','cacar'=>'Cacar Air'][$d['hasil']] ?? $d['hasil'];
                                ?>
                                <span class="badge <?= $badgeClass ?>"><?= $label ?></span>
                            </td>
                            <td><?= $d['confidence'] ?>%</td>
                            <td>
                                <a href="/user/result.php?id=<?= $d['id'] ?>" class="btn btn-secondary btn-sm">
                                    <i class="ti ti-eye"></i>
                                </a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <?php endif; ?>
        </div>
    </div>
</div>
</body>
</html>
