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
</head>
<body>
  <div class="app-container">
    
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <img src="https://api.iconify.design/carbon:network-4.svg?color=%230b4bcc" alt="Logo" class="sidebar-logo">
        <div>
          <h2 class="sidebar-title">DermDetect</h2>
          <span class="sidebar-subtitle">Clinical Portal</span>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <a href="/user/dashboard.php" class="nav-item active">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
          Dashboard
        </a>
        <a href="/user/diagnose.php" class="nav-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
          Diagnosis
        </a>
        <a href="/user/history.php" class="nav-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          History
        </a>
      </nav>
      
      <div class="sidebar-footer">
        <a href="/logout.php" class="nav-item logout-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          Sign Out
        </a>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      
      <!-- Topbar -->
      <header class="topbar">
        <div class="topbar-nav">
          <a href="/user/dashboard.php" class="topbar-link active">Dashboard</a>
          <a href="/user/diagnose.php" class="topbar-link">Diagnosis</a>
          <a href="/user/history.php" class="topbar-link">History</a>
        </div>
        <div class="user-profile">
          <div class="avatar" style="display:flex; align-items:center; justify-content:center; background:var(--primary-color); color:white; font-size:12px; font-weight:bold;">
            <?= strtoupper(substr($user['nama'], 0, 2)) ?>
          </div>
        </div>
      </header>
      
      <!-- Page Content -->
      <div class="page-content">
        
        <?php if ($flash): ?>
        <div style="background-color: <?= $flash['type'] === 'success' ? 'var(--success-color)' : 'var(--warning-bg)' ?>; color: <?= $flash['type'] === 'success' ? 'white' : 'var(--warning-text)' ?>; padding: 1rem; border-radius: var(--radius-md); margin-bottom: 2rem;">
            <?= htmlspecialchars($flash['message']) ?>
        </div>
        <?php endif; ?>

        <div class="page-header">
          <div>
            <h1 class="page-title">Selamat datang, <?= htmlspecialchars($user['nama']) ?>!</h1>
            <p class="page-subtitle">Ringkasan aktivitas diagnosis Anda.</p>
          </div>
          <a href="/user/diagnose.php" class="btn-primary" style="text-decoration: none;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Diagnosis Baru
          </a>
        </div>
        
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon icon-blue">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </div>
            <div class="stat-info">
              <h3>Total Diagnosis</h3>
              <p><?= $stat['total'] ?? 0 ?></p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon icon-red">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            </div>
            <div class="stat-info">
              <h3>Campak</h3>
              <p><?= $stat['campak'] ?? 0 ?></p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon icon-gray" style="background-color: #fef3c7; color: #b45309;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="stat-info">
              <h3>Rubella</h3>
              <p><?= $stat['rubella'] ?? 0 ?></p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon icon-gray" style="background-color: #dcfce7; color: #15803d;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="stat-info">
              <h3>Cacar Air</h3>
              <p><?= $stat['cacar'] ?? 0 ?></p>
            </div>
          </div>
        </div>
        
        <!-- Data Table (Riwayat Terbaru) -->
        <div class="data-card">
          <div class="table-header">
            <h3 style="font-size: 1rem; color: var(--text-primary); font-weight: 600;">Riwayat Terbaru</h3>
            <a href="/user/history.php" class="btn-outline" style="padding: 0.25rem 0.75rem; font-size: 0.75rem; text-decoration: none;">Lihat Semua</a>
          </div>
          
          <?php if (empty($riwayat)): ?>
          <div style="text-align: center; padding: 4rem;">
            <p style="color: var(--text-secondary);">Belum ada riwayat diagnosis.</p>
          </div>
          <?php else: ?>
          <div style="overflow-x: auto;">
            <table>
              <thead>
                <tr>
                  <th>Tanggal</th>
                  <th>Hasil</th>
                  <th>Keyakinan</th>
                  <th>Aksi</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($riwayat as $d): ?>
                <tr>
                  <td><?= date('d M Y', strtotime($d['created_at'])) ?></td>
                  <td>
                    <?php
                    $badgeClass = ['campak'=>'badge-blue','rubella'=>'badge-red','cacar'=>'badge-gray'][$d['hasil']] ?? 'badge-gray';
                    $label = ['campak'=>'Campak','rubella'=>'Rubella','cacar'=>'Cacar Air'][$d['hasil']] ?? $d['hasil'];
                    ?>
                    <span class="badge <?= $badgeClass ?>"><?= $label ?></span>
                  </td>
                  <td>
                    <div class="confidence-bar">
                      <div class="bar-bg"><div class="bar-fill <?= $badgeClass === 'badge-red' ? 'fill-red' : 'fill-blue' ?>" style="width: <?= $d['confidence'] ?>%;"></div></div>
                      <span class="confidence-val"><?= $d['confidence'] ?>%</span>
                    </div>
                  </td>
                  <td><a href="/user/result.php?id=<?= $d['id'] ?>" class="action-link" style="text-decoration:none;">Detail</a></td>
                </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
          <?php endif; ?>
        </div>
        
      </div>
    </main>
  </div>
</body>
</html>
