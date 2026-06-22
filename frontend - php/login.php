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
</head>
<body>
  <div class="auth-container">
    <div class="auth-card">
      <img src="https://api.iconify.design/carbon:network-4.svg?color=%230b4bcc" alt="DermDetect Logo" class="auth-logo">
      <h1 class="auth-title">DermDetect</h1>
      <p class="auth-subtitle">Sistem Klasifikasi Penyakit Ruam Kulit</p>

      <?php if ($error): ?>
      <div style="background-color: var(--warning-bg); color: var(--warning-text); padding: 0.75rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.875rem; text-align: left;">
          <?= htmlspecialchars($error) ?>
      </div>
      <?php endif; ?>
      
      <form method="POST">
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input type="email" id="email" name="email" class="form-input" placeholder="email@contoh.com" value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <div class="input-icon-wrapper">
            <input type="password" id="password" name="password" class="form-input" placeholder="••••••••" required>
            <span class="input-icon" onclick="const p = document.getElementById('password'); p.type = p.type === 'password' ? 'text' : 'password';">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            </span>
          </div>
          <a href="#" class="link-right">Lupa password?</a>
        </div>
        
        <button type="submit" class="btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
            <polyline points="10 17 15 12 10 7"></polyline>
            <line x1="15" y1="12" x2="3" y2="12"></line>
          </svg>
          Masuk
        </button>
      </form>
      
      <div class="auth-divider">ATAU</div>
      
      <div class="auth-footer">
        Belum punya akun? <a href="/register.php">Daftar sekarang</a>
      </div>
    </div>
  </div>
</body>
</html>
