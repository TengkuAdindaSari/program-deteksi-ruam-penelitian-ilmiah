<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$user    = getUser();
$token   = getToken();
$page    = (int)($_GET['page'] ?? 1);
$keyword = $_GET['keyword'] ?? '';
$error   = '';
$success = '';

// Tambah user baru
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'create') {
    $res = Api::post('/admin/users', [
        'nama'     => $_POST['nama'],
        'email'    => $_POST['email'],
        'password' => $_POST['password'],
        'role'     => $_POST['role'],
    ], $token);
    if ($res['success'] ?? false) {
        flash('success', 'User berhasil ditambahkan!');
        header('Location: /admin/users.php');
        exit;
    } else {
        $error = $res['message'] ?? 'Gagal menambah user';
    }
}

// Hapus user
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete') {
    $uid = (int)$_POST['user_id'];
    $res = Api::delete("/admin/users/$uid", $token);
    if ($res['success'] ?? false) {
        flash('success', 'User berhasil dihapus.');
    } else {
        flash('danger', $res['message'] ?? 'Gagal menghapus user');
    }
    header('Location: /admin/users.php');
    exit;
}

$query = "/admin/users?page=$page&per_page=15";
if ($keyword) $query .= "&keyword=" . urlencode($keyword);
$res   = Api::get($query, $token);
$users = $res['data'] ?? [];
$meta  = $res['meta'] ?? [];
$flash = getFlash();
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kelola User — Admin DermDetect</title>
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
                <a href="/admin/users.php" class="active"><i class="ti ti-users"></i> Kelola User</a>
                <a href="/admin/models.php"><i class="ti ti-cpu"></i> Kelola Model</a>
                <a href="/admin/stats.php"><i class="ti ti-chart-bar"></i> Statistik</a>
            </div>
        </div>

        <div>
            <h2 class="page-title">Kelola User</h2>

            <?php if ($flash): ?>
            <div class="alert alert-<?= $flash['type']==='success'?'success':'danger' ?>">
                <?= htmlspecialchars($flash['message']) ?>
            </div>
            <?php endif; ?>

            <div class="grid-2 mb-4">
                <!-- Form Tambah User -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-user-plus" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Tambah User Baru</h3>
                    </div>
                    <div class="card-body">
                        <?php if ($error): ?>
                        <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
                        <?php endif; ?>
                        <form method="POST">
                            <input type="hidden" name="action" value="create">
                            <div class="form-group">
                                <label class="form-label">Nama Lengkap</label>
                                <input type="text" name="nama" class="form-control" required placeholder="Nama user">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Email</label>
                                <input type="email" name="email" class="form-control" required placeholder="email@contoh.com">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required placeholder="Min. 6 karakter">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Role</label>
                                <select name="role" class="form-control">
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">
                                <i class="ti ti-plus"></i> Tambah User
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Filter -->
                <div class="card" style="height:fit-content;">
                    <div class="card-header">
                        <i class="ti ti-search" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Cari User</h3>
                    </div>
                    <div class="card-body">
                        <form method="GET">
                            <div class="form-group">
                                <label class="form-label">Nama atau Email</label>
                                <input type="text" name="keyword" class="form-control"
                                       placeholder="Ketik nama/email..." value="<?= htmlspecialchars($keyword) ?>">
                            </div>
                            <div class="flex gap-2">
                                <button type="submit" class="btn btn-primary">
                                    <i class="ti ti-search"></i> Cari
                                </button>
                                <a href="/admin/users.php" class="btn btn-secondary">Reset</a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Tabel User -->
            <div class="card">
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Nama</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Total Diagnosis</th>
                                <th>Bergabung</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($users as $u): ?>
                            <tr>
                                <td class="text-muted"><?= $u['id'] ?></td>
                                <td style="font-weight:500;"><?= htmlspecialchars($u['nama']) ?></td>
                                <td class="text-muted"><?= htmlspecialchars($u['email']) ?></td>
                                <td>
                                    <span class="badge <?= $u['role']==='admin'?'badge-red':'badge-blue' ?>">
                                        <?= ucfirst($u['role']) ?>
                                    </span>
                                </td>
                                <td><?= $u['total_diagnosis'] ?? 0 ?></td>
                                <td class="text-muted"><?= date('d M Y', strtotime($u['created_at'])) ?></td>
                                <td>
                                    <?php if ($u['id'] != $user['id']): ?>
                                    <form method="POST" onsubmit="return confirm('Hapus user <?= htmlspecialchars($u['nama']) ?>?')">
                                        <input type="hidden" name="action" value="delete">
                                        <input type="hidden" name="user_id" value="<?= $u['id'] ?>">
                                        <button type="submit" class="btn btn-danger btn-sm">
                                            <i class="ti ti-trash"></i>
                                        </button>
                                    </form>
                                    <?php else: ?>
                                    <span class="text-sm text-muted">—</span>
                                    <?php endif; ?>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
                <div class="pagination">
                    <div class="pagination-info">Total: <?= $meta['total'] ?? 0 ?> user</div>
                    <div class="pagination-btns">
                        <?php for ($i=1; $i<=($meta['pages']??1); $i++): ?>
                        <a href="?page=<?= $i ?>&keyword=<?= urlencode($keyword) ?>"
                           class="page-btn <?= $i==$page?'active':'' ?>"><?= $i ?></a>
                        <?php endfor; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
