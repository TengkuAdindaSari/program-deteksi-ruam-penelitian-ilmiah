<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$user  = getUser();
$token = getToken();
$error = '';

// Upload model baru
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action']??'') === 'upload') {
    if (empty($_FILES['model_file']['tmp_name'])) {
        $error = 'File model wajib diupload';
    } else {
        $data = [
            'versi'      => $_POST['versi'],
            'akurasi'    => $_POST['akurasi'],
            'f1_score'   => $_POST['f1_score'],
            'keterangan' => $_POST['keterangan'],
        ];
        $res = Api::post('/admin/models/upload', $data, $token, ['model_file' => $_FILES['model_file']]);
        if ($res['success'] ?? false) {
            flash('success', 'Model berhasil diupload!');
            header('Location: /admin/models.php');
            exit;
        } else {
            $error = $res['message'] ?? 'Gagal upload model';
        }
    }
}

// Aktifkan model
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action']??'') === 'activate') {
    $mid = (int)$_POST['model_id'];
    $res = Api::put("/admin/models/$mid/activate", [], $token);
    flash($res['success']??false ? 'success' : 'danger',
          $res['message'] ?? 'Gagal mengaktifkan model');
    header('Location: /admin/models.php');
    exit;
}

// Hapus model
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action']??'') === 'delete') {
    $mid = (int)$_POST['model_id'];
    $res = Api::delete("/admin/models/$mid", $token);
    flash($res['success']??false ? 'success' : 'danger',
          $res['message'] ?? 'Gagal menghapus model');
    header('Location: /admin/models.php');
    exit;
}

$res    = Api::get('/admin/models', $token);
$models = $res['data'] ?? [];
$flash  = getFlash();
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kelola Model — Admin DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<nav class="navbar" style="border-bottom-color:#FECACA;">
    <div class="navbar-brand" style="color:#DC2626;"><i class="ti ti-shield-check"></i> DermDetect Admin</div>
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
                <a href="/admin/diagnoses.php"><i class="ti ti-history"></i> Histori Diagnosis</a>
                <a href="/admin/users.php"><i class="ti ti-users"></i> Kelola User</a>
                <a href="/admin/models.php" class="active"><i class="ti ti-cpu"></i> Kelola Model</a>
                <a href="/admin/stats.php"><i class="ti ti-chart-bar"></i> Statistik</a>
            </div>
        </div>

        <div>
            <h2 class="page-title">Kelola Model AI</h2>

            <?php if ($flash): ?>
            <div class="alert alert-<?= $flash['type']==='success'?'success':'danger' ?>">
                <?= htmlspecialchars($flash['message']) ?>
            </div>
            <?php endif; ?>

            <div class="grid-2 mb-4">
                <!-- Upload Model -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-upload" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Upload Model Baru</h3>
                    </div>
                    <div class="card-body">
                        <?php if ($error): ?>
                        <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
                        <?php endif; ?>
                        <form method="POST" enctype="multipart/form-data">
                            <input type="hidden" name="action" value="upload">
                            <div class="form-group">
                                <label class="form-label">File Model (.keras / .h5)</label>
                                <input type="file" name="model_file" class="form-control" accept=".keras,.h5" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Versi</label>
                                <input type="text" name="versi" class="form-control" placeholder="contoh: v2.0" required>
                            </div>
                            <div class="grid-2">
                                <div class="form-group">
                                    <label class="form-label">Akurasi (0-1)</label>
                                    <input type="number" name="akurasi" class="form-control"
                                           step="0.001" min="0" max="1" placeholder="0.931">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">F1-Score (0-1)</label>
                                    <input type="number" name="f1_score" class="form-control"
                                           step="0.001" min="0" max="1" placeholder="0.930">
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Keterangan</label>
                                <input type="text" name="keterangan" class="form-control"
                                       placeholder="Deskripsi singkat model">
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">
                                <i class="ti ti-upload"></i> Upload Model
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Info -->
                <div class="card" style="height:fit-content;">
                    <div class="card-header">
                        <i class="ti ti-info-circle" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Panduan</h3>
                    </div>
                    <div class="card-body">
                        <div class="flex gap-2 mb-3">
                            <i class="ti ti-circle-check" style="color:#10B981;flex-shrink:0;"></i>
                            <span class="text-sm">Upload file <strong>.keras</strong> atau <strong>.h5</strong> hasil training.</span>
                        </div>
                        <div class="flex gap-2 mb-3">
                            <i class="ti ti-circle-check" style="color:#10B981;flex-shrink:0;"></i>
                            <span class="text-sm">Setelah upload, klik <strong>Aktifkan</strong> untuk menggunakan model pada prediksi.</span>
                        </div>
                        <div class="flex gap-2 mb-3">
                            <i class="ti ti-circle-check" style="color:#10B981;flex-shrink:0;"></i>
                            <span class="text-sm">Hanya satu model yang bisa aktif pada satu waktu.</span>
                        </div>
                        <div class="flex gap-2">
                            <i class="ti ti-alert-triangle" style="color:#F59E0B;flex-shrink:0;"></i>
                            <span class="text-sm">Model aktif tidak bisa dihapus. Aktifkan model lain dulu sebelum menghapus.</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Daftar Model -->
            <div class="card">
                <div class="card-header">
                    <i class="ti ti-versions" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Riwayat Versi Model</h3>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Versi</th>
                                <th>File</th>
                                <th>Akurasi</th>
                                <th>F1-Score</th>
                                <th>Keterangan</th>
                                <th>Diupload</th>
                                <th>Status</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($models as $m): ?>
                            <tr>
                                <td style="font-weight:600;"><?= htmlspecialchars($m['versi']) ?></td>
                                <td class="text-muted text-sm"><?= htmlspecialchars($m['nama_file']) ?></td>
                                <td style="color:#10B981;font-weight:500;">
                                    <?= $m['akurasi'] ? round($m['akurasi']*100,1).'%' : '-' ?>
                                </td>
                                <td><?= $m['f1_score'] ?? '-' ?></td>
                                <td class="text-muted text-sm"><?= htmlspecialchars($m['keterangan'] ?? '-') ?></td>
                                <td class="text-muted"><?= date('d M Y', strtotime($m['created_at'])) ?></td>
                                <td>
                                    <span class="badge <?= $m['is_active'] ? 'badge-green' : 'badge-gray' ?>">
                                        <?= $m['is_active'] ? 'Aktif' : 'Arsip' ?>
                                    </span>
                                </td>
                                <td>
                                    <div class="flex gap-2">
                                        <?php if (!$m['is_active']): ?>
                                        <form method="POST">
                                            <input type="hidden" name="action" value="activate">
                                            <input type="hidden" name="model_id" value="<?= $m['id'] ?>">
                                            <button type="submit" class="btn btn-success btn-sm">
                                                <i class="ti ti-player-play"></i> Aktifkan
                                            </button>
                                        </form>
                                        <form method="POST" onsubmit="return confirm('Hapus model ini?')">
                                            <input type="hidden" name="action" value="delete">
                                            <input type="hidden" name="model_id" value="<?= $m['id'] ?>">
                                            <button type="submit" class="btn btn-danger btn-sm">
                                                <i class="ti ti-trash"></i>
                                            </button>
                                        </form>
                                        <?php else: ?>
                                        <span class="text-sm text-muted">Sedang digunakan</span>
                                        <?php endif; ?>
                                    </div>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
