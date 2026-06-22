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
        <a href="/user/dashboard.php" class="nav-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
          Dashboard
        </a>
        <a href="/user/diagnose.php" class="nav-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
          Diagnosis
        </a>
        <a href="/user/history.php" class="nav-item active">
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
          <a href="/user/dashboard.php" class="topbar-link">Dashboard</a>
          <a href="/user/diagnose.php" class="topbar-link">Diagnosis</a>
          <a href="/user/history.php" class="topbar-link active">History</a>
        </div>
        <div class="user-profile">
          <div class="avatar" style="display:flex; align-items:center; justify-content:center; background:var(--primary-color); color:white; font-size:12px; font-weight:bold;">
            <?= strtoupper(substr($user['nama'], 0, 2)) ?>
          </div>
        </div>
      </header>
      
      <!-- Page Content -->
      <div class="page-content">
        
        <div class="breadcrumbs">
          <span>Dashboard</span> / <span class="active">Riwayat Diagnosis</span>
        </div>
        
        <div class="page-header">
          <div>
            <h1 class="page-title">Riwayat Diagnosis Saya</h1>
            <p class="page-subtitle">Kelola dan tinjau data hasil pemeriksaan kulit secara berkala.</p>
          </div>
          <a href="/user/diagnose.php" class="btn-primary" style="text-decoration:none;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Diagnosis Baru
          </a>
        </div>
        
        <!-- Data Table -->
        <div class="data-card">
          <div class="table-header">
            <div class="search-box">
              <span class="search-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              </span>
              <input type="text" placeholder="Cari hasil atau tanggal...">
            </div>
            <div class="table-actions">
              <button class="icon-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
              </button>
              <button class="icon-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              </button>
            </div>
          </div>
          
          <?php if (empty($diagnoses)): ?>
          <div style="text-align: center; padding: 4rem;">
            <p style="color: var(--text-secondary);">Belum ada riwayat diagnosis.</p>
          </div>
          <?php else: ?>
          <div style="overflow-x: auto;">
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
                  <td><?= (($page-1)*10) + $i + 1 ?></td>
                  <td><?= date('d M Y, H:i', strtotime($d['created_at'])) ?></td>
                  <td>
                    <span class="badge <?= $badgeMap[$d['hasil']] ?? 'badge-gray' ?>">
                        <?= $labelMap[$d['hasil']] ?? $d['hasil'] ?>
                    </span>
                  </td>
                  <td>
                    <div class="confidence-bar">
                      <div class="bar-bg"><div class="bar-fill <?= ($badgeMap[$d['hasil']] ?? 'badge-gray') === 'badge-blue' ? 'fill-blue' : 'fill-red' ?>" style="width: <?= $d['confidence'] ?>%;"></div></div>
                      <span class="confidence-val"><?= $d['confidence'] ?>%</span>
                    </div>
                  </td>
                  <td>
                    <span class="status">
                      <span class="status-dot <?= $d['status']==='selesai' ? 'dot-blue' : 'dot-gray' ?>"></span> 
                      <?= ucfirst($d['status']) ?>
                    </span>
                  </td>
                  <td><a href="/user/result.php?id=<?= $d['id'] ?>" class="action-link" style="text-decoration:none;">Detail</a></td>
                </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
          
          <div class="pagination">
            <span>Menampilkan <?= count($diagnoses) ?> dari <?= $meta['total'] ?? 0 ?> riwayat</span>
            <div class="page-numbers">
              <?php if ($page > 1): ?>
              <a href="?page=<?= $page-1 ?>" class="page-btn" style="text-decoration:none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </a>
              <?php endif; ?>
              
              <?php for ($i = 1; $i <= ($meta['pages'] ?? 1); $i++): ?>
              <a href="?page=<?= $i ?>" class="page-btn <?= $i==$page ? 'active' : '' ?>" style="text-decoration:none;"><?= $i ?></a>
              <?php endfor; ?>
              
              <?php if ($page < ($meta['pages'] ?? 1)): ?>
              <a href="?page=<?= $page+1 ?>" class="page-btn" style="text-decoration:none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </a>
              <?php endif; ?>
            </div>
          </div>
          <?php endif; ?>
        </div>
        
      </div>
    </main>
  </div>
</body>
</html>
