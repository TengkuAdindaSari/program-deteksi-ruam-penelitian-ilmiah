<?php
require_once 'includes/auth.php';
require_once 'includes/api.php';
requireGuest();

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email    = trim($_POST['email'] ?? '');
    $password = trim($_POST['password'] ?? '');

    if ($email && $password) {
        $res = Api::post('/auth/login', [
            'email'    => $email,
            'password' => $password,
        ]);

        if ($res['success'] ?? false) {
            setSession($res['token'], $res['user']);
            if ($res['user']['role'] === 'admin') {
                header('Location: /admin/dashboard.php');
            } else {
                header('Location: /user/dashboard.php');
            }
            exit;
        } else {
            $error = $res['message'] ?? 'Login gagal';
        }
    } else {
        $error = 'Email dan password wajib diisi';
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>
<div class="login-wrapper">
    <div class="login-card">
        <div class="login-logo">
            <i class="ti ti-stethoscope"></i>
            <h1>DermDetect</h1>
            <p>Sistem Klasifikasi Penyakit Ruam Kulit</p>
        </div>

        <?php if ($error): ?>
        <div class="alert alert-danger">
            <i class="ti ti-alert-circle"></i> <?= htmlspecialchars($error) ?>
        </div>
        <?php endif; ?>

        <form method="POST">
            <div class="form-group">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control"
                       placeholder="email@contoh.com"
                       value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control"
                       placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block">
                <i class="ti ti-login"></i> Masuk
            </button>
        </form>

        <hr class="divider">
        <p class="text-sm text-muted" style="text-align:center;">
            Belum punya akun?
            <a href="/register.php">Daftar sekarang</a>
        </p>
    </div>
</div>
</body>
</html>
