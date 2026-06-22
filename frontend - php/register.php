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
</head>
<body>
  <div class="auth-container">
    <div class="auth-card">
      <img src="https://api.iconify.design/carbon:network-4.svg?color=%230b4bcc" alt="DermDetect Logo" class="auth-logo">
      <h1 class="auth-title">DermDetect</h1>
      <p class="auth-subtitle">Buat akun baru</p>

      <?php if ($error): ?>
      <div style="background-color: var(--warning-bg); color: var(--warning-text); padding: 0.75rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.875rem; text-align: left;">
          <?= htmlspecialchars($error) ?>
      </div>
      <?php endif; ?>
      
      <form method="POST">
        <div class="form-group">
          <label class="form-label" for="nama">Nama Lengkap</label>
          <input type="text" id="nama" name="nama" class="form-input" placeholder="Nama lengkap Anda" value="<?= htmlspecialchars($_POST['nama'] ?? '') ?>" required>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input type="email" id="email" name="email" class="form-input" placeholder="email@contoh.com" value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input type="password" id="password" name="password" class="form-input" placeholder="Minimal 6 karakter" required>
        </div>
        
        <div class="form-group" style="margin-bottom: 2rem;">
          <label class="form-label" for="konfirm">Konfirmasi Password</label>
          <input type="password" id="konfirm" name="konfirm" class="form-input" placeholder="Ulangi password" required>
        </div>
        
        <button type="submit" class="btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
          Daftar Sekarang
        </button>
      </form>
      
      <div class="auth-divider">ATAU</div>
      
      <div class="auth-footer">
        Sudah punya akun? <a href="/login.php">Login di sini</a>
      </div>
    </div>
  </div>
</body>
</html>
