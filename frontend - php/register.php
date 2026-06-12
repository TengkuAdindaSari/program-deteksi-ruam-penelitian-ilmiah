<?php
require_once 'includes/auth.php';
require_once 'includes/api.php';
requireGuest();

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nama     = trim($_POST['nama'] ?? '');
    $email    = trim($_POST['email'] ?? '');
    $password = trim($_POST['password'] ?? '');
    $konfirm  = trim($_POST['konfirm'] ?? '');

    if (!$nama || !$email || !$password) {
        $error = 'Semua field wajib diisi';
    } elseif ($password !== $konfirm) {
        $error = 'Konfirmasi password tidak cocok';
    } elseif (strlen($password) < 6) {
        $error = 'Password minimal 6 karakter';
    } else {
        $res = Api::post('/auth/register', [
            'nama'     => $nama,
            'email'    => $email,
            'password' => $password,
        ]);

        if ($res['success'] ?? false) {
            flash('success', 'Registrasi berhasil! Silakan login.');
            header('Location: /login.php');
            exit;
        } else {
            $error = $res['message'] ?? 'Registrasi gagal';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daftar — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>
<div class="login-wrapper">
    <div class="login-card">
        <div class="login-logo">
            <i class="ti ti-stethoscope"></i>
            <h1>DermDetect</h1>
            <p>Buat akun baru</p>
        </div>

        <?php if ($error): ?>
        <div class="alert alert-danger">
            <i class="ti ti-alert-circle"></i> <?= htmlspecialchars($error) ?>
        </div>
        <?php endif; ?>

        <form method="POST">
            <div class="form-group">
                <label class="form-label">Nama Lengkap</label>
                <input type="text" name="nama" class="form-control"
                       placeholder="Nama lengkap Anda"
                       value="<?= htmlspecialchars($_POST['nama'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control"
                       placeholder="email@contoh.com"
                       value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control"
                       placeholder="Minimal 6 karakter" required>
            </div>
            <div class="form-group">
                <label class="form-label">Konfirmasi Password</label>
                <input type="password" name="konfirm" class="form-control"
                       placeholder="Ulangi password" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block">
                <i class="ti ti-user-plus"></i> Daftar Sekarang
            </button>
        </form>

        <hr class="divider">
        <p class="text-sm text-muted" style="text-align:center;">
            Sudah punya akun? <a href="/login.php">Login di sini</a>
        </p>
    </div>
</div>
</body>
</html>
