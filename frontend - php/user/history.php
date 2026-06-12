<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();

$user  = getUser();
$token = getToken();
$page  = (int)($_GET['page'] ?? 1);

$res      = Api::get("/diagnose/history?page=$page&per_page=10", $token);
$diagnoses = $res['data'] ?? [];
$meta      = $res['meta'] ?? [];

$labelMap = ['campak'=>'Campak','rubella'=>'Rubella','cacar'=>'Cacar Air'];
$badgeMap = ['campak'=>'badge-blue','rubella'=>'badge-amber','cacar'=>'badge-green'];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riwayat Diagnosis — DermDetect</title>
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
        <h2 class="page-title" style="margin:0;">Riwayat Diagnosis Saya</h2>
        <a href="/user/diagnose.php" class="btn btn-primary btn-sm ml-auto">
            <i class="ti ti-plus"></i> Diagnosis Baru
        </a>
    </div>

    <div class="card">
        <?php if (empty($diagnoses)): ?>
        <div class="card-body" style="text-align:center;padding:48px;">
            <i class="ti ti-file-off" style="font-size:48px;color:#9CA3AF;display:block;margin-bottom:12px;"></i>
            <p class="text-muted">Belum ada riwayat diagnosis.</p>
            <a href="/user/diagnose.php" class="btn btn-primary mt-3">
                <i class="ti ti-upload"></i> Mulai Diagnosis Pertama
            </a>
        </div>
        <?php else: ?>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Tanggal</th>
                        <th>Hasil</th>
                        <th>Keyakinan</th>
                        <th>Status</th>
                        <th>Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($diagnoses as $i => $d): ?>
                    <tr>
                        <td class="text-muted"><?= (($page-1)*10) + $i + 1 ?></td>
                        <td><?= date('d M Y, H:i', strtotime($d['created_at'])) ?></td>
                        <td>
                            <span class="badge <?= $badgeMap[$d['hasil']] ?? 'badge-gray' ?>">
                                <?= $labelMap[$d['hasil']] ?? $d['hasil'] ?>
                            </span>
                        </td>
                        <td><strong><?= $d['confidence'] ?>%</strong></td>
                        <td>
                            <span class="badge <?= $d['status']==='selesai' ? 'badge-green' : 'badge-amber' ?>">
                                <?= ucfirst($d['status']) ?>
                            </span>
                        </td>
                        <td>
                            <a href="/user/result.php?id=<?= $d['id'] ?>" class="btn btn-secondary btn-sm">
                                <i class="ti ti-eye"></i> Detail
                            </a>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div class="pagination">
            <div class="pagination-info">
                Menampilkan <?= count($diagnoses) ?> dari <?= $meta['total'] ?? 0 ?> hasil
            </div>
            <div class="pagination-btns">
                <?php if ($page > 1): ?>
                <a href="?page=<?= $page-1 ?>" class="page-btn">←</a>
                <?php endif; ?>
                <?php for ($i = 1; $i <= ($meta['pages'] ?? 1); $i++): ?>
                <a href="?page=<?= $i ?>" class="page-btn <?= $i==$page ? 'active' : '' ?>"><?= $i ?></a>
                <?php endfor; ?>
                <?php if ($page < ($meta['pages'] ?? 1)): ?>
                <a href="?page=<?= $page+1 ?>" class="page-btn">→</a>
                <?php endif; ?>
            </div>
        </div>
        <?php endif; ?>
    </div>
</div>
</body>
</html>
