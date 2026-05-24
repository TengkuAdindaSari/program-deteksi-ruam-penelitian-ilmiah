<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$user    = getUser();
$token   = getToken();
$page    = (int)($_GET['page']    ?? 1);
$keyword = $_GET['keyword'] ?? '';
$hasil   = $_GET['hasil']   ?? '';

$query = "/admin/diagnoses?page=$page&per_page=15";
if ($keyword) $query .= "&keyword=" . urlencode($keyword);
if ($hasil)   $query .= "&hasil=$hasil";

$res       = Api::get($query, $token);
$diagnoses = $res['data'] ?? [];
$meta      = $res['meta'] ?? [];

$labelMap = ['campak'=>'Campak','rubella'=>'Rubella','cacar'=>'Cacar Air'];
$badgeMap = ['campak'=>'badge-blue','rubella'=>'badge-amber','cacar'=>'badge-green'];
$flash    = getFlash();
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Histori Diagnosis — Admin DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<nav class="navbar" style="border-bottom-color:#FECACA;">
    <div class="navbar-brand" style="color:#DC2626;">
        <i class="ti ti-shield-check"></i> DermDetect Admin
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:8px;">
        <span class="badge badge-red">Administrator</span>
        <div class="nav-avatar" style="background:#FEF2F2;color:#DC2626;"><?= strtoupper(substr($user['nama'],0,2)) ?></div>
        <a href="/logout.php" class="btn btn-secondary btn-sm"><i class="ti ti-logout"></i> Keluar</a>
    </div>
</nav>

<div class="container">
    <div class="admin-layout">
        <div class="sidebar">
            <div class="sidebar-header"><p>Panel Admin</p><h4><?= htmlspecialchars($user['nama']) ?></h4></div>
            <div class="sidebar-nav">
                <a href="/admin/dashboard.php"><i class="ti ti-layout-dashboard"></i> Dashboard</a>
                <a href="/admin/diagnoses.php" class="active"><i class="ti ti-history"></i> Histori Diagnosis</a>
                <a href="/admin/users.php"><i class="ti ti-users"></i> Kelola User</a>
                <a href="/admin/models.php"><i class="ti ti-cpu"></i> Kelola Model</a>
                <a href="/admin/stats.php"><i class="ti ti-chart-bar"></i> Statistik</a>
            </div>
        </div>

        <div>
            <h2 class="page-title">Histori Diagnosis</h2>

            <?php if ($flash): ?>
            <div class="alert alert-<?= $flash['type']==='success'?'success':'danger' ?>">
                <?= htmlspecialchars($flash['message']) ?>
            </div>
            <?php endif; ?>

            <!-- Filter -->
            <div class="card mb-4">
                <div class="card-body" style="padding:14px;">
                    <form method="GET" class="flex gap-2 items-center flex-wrap">
                        <input type="text" name="keyword" class="form-control" style="max-width:200px;"
                               placeholder="Cari nama user..." value="<?= htmlspecialchars($keyword) ?>">
                        <select name="hasil" class="form-control" style="max-width:160px;">
                            <option value="">Semua kelas</option>
                            <option value="campak"  <?= $hasil==='campak'  ?'selected':'' ?>>Campak</option>
                            <option value="rubella" <?= $hasil==='rubella' ?'selected':'' ?>>Rubella</option>
                            <option value="cacar"   <?= $hasil==='cacar'   ?'selected':'' ?>>Cacar Air</option>
                        </select>
                        <button type="submit" class="btn btn-primary">
                            <i class="ti ti-search"></i> Cari
                        </button>
                        <a href="/admin/diagnoses.php" class="btn btn-secondary">Reset</a>
                    </form>
                </div>
            </div>

            <!-- Tabel -->
            <div class="card">
                <?php if (empty($diagnoses)): ?>
                <div class="card-body" style="text-align:center;padding:48px;">
                    <i class="ti ti-file-off" style="font-size:48px;color:#9CA3AF;display:block;margin-bottom:12px;"></i>
                    <p class="text-muted">Tidak ada data ditemukan.</p>
                </div>
                <?php else: ?>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>User</th>
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
                                <td class="text-muted"><?= $d['id'] ?></td>
                                <td style="font-weight:500;"><?= htmlspecialchars($d['user_nama'] ?? '-') ?></td>
                                <td><?= date('d M Y', strtotime($d['created_at'])) ?></td>
                                <td>
                                    <span class="badge <?= $badgeMap[$d['hasil']] ?? 'badge-gray' ?>">
                                        <?= $labelMap[$d['hasil']] ?? $d['hasil'] ?>
                                    </span>
                                </td>
                                <td><strong><?= $d['confidence'] ?>%</strong></td>
                                <td>
                                    <span class="badge <?= $d['status']==='selesai'?'badge-green':($d['status']==='review'?'badge-amber':'badge-red') ?>">
                                        <?= ucfirst($d['status']) ?>
                                    </span>
                                </td>
                                <td>
                                    <div class="flex gap-2">
                                        <a href="/admin/diagnosis-detail.php?id=<?= $d['id'] ?>"
                                           class="btn btn-secondary btn-sm">
                                            <i class="ti ti-eye"></i>
                                        </a>
                                        <form method="POST" action="/admin/diagnosis-action.php"
                                              onsubmit="return confirm('Hapus diagnosis ini?')">
                                            <input type="hidden" name="id" value="<?= $d['id'] ?>">
                                            <input type="hidden" name="action" value="delete">
                                            <button type="submit" class="btn btn-danger btn-sm">
                                                <i class="ti ti-trash"></i>
                                            </button>
                                        </form>
                                    </div>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
                <div class="pagination">
                    <div class="pagination-info">
                        Menampilkan <?= count($diagnoses) ?> dari <?= $meta['total'] ?? 0 ?> hasil
                    </div>
                    <div class="pagination-btns">
                        <?php if ($page > 1): ?>
                        <a href="?page=<?= $page-1 ?>&keyword=<?= urlencode($keyword) ?>&hasil=<?= $hasil ?>" class="page-btn">←</a>
                        <?php endif; ?>
                        <?php for ($i=1; $i<=($meta['pages']??1); $i++): ?>
                        <a href="?page=<?= $i ?>&keyword=<?= urlencode($keyword) ?>&hasil=<?= $hasil ?>"
                           class="page-btn <?= $i==$page?'active':'' ?>"><?= $i ?></a>
                        <?php endfor; ?>
                        <?php if ($page < ($meta['pages']??1)): ?>
                        <a href="?page=<?= $page+1 ?>&keyword=<?= urlencode($keyword) ?>&hasil=<?= $hasil ?>" class="page-btn">→</a>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>
</body>
</html>
