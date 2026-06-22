<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();

$user  = getUser();
$token = getToken();
$id    = (int)($_GET['id'] ?? 0);

$res = Api::get("/diagnose/history/$id", $token);
$d   = $res['data'] ?? null;

if (!$d) {
    flash('danger', 'Data diagnosis tidak ditemukan.');
    header('Location: /user/history.php');
    exit;
}

// Ambil triple result dari database, fallback ke session jika tidak ada
$triple = $d['triple'] ?? null;
if (!$triple) {
    $tripleKey = 'triple_result_' . $id;
    $triple    = $_SESSION[$tripleKey] ?? null;
    unset($_SESSION[$tripleKey]);
}

$infoMap = [
    'campak'  => [
        'label'     => 'Campak',
        'icon'      => '🔴',
        'class'     => 'campak',
        'badge'     => 'badge-blue',
        'color'     => '#2563EB',
        'gejala'    => ['Demam tinggi 38-40°C', 'Batuk kering', 'Mata merah (konjungtivitis)', 'Ruam merah menyebar dari wajah ke badan', 'Bercak Koplik di mulut'],
        'penanganan'=> 'Istirahat dan cukup cairan. Konsultasikan ke dokter. Vaksin MMR untuk pencegahan.',
    ],
    'rubella' => [
        'label'     => 'Rubella',
        'icon'      => '🟠',
        'class'     => 'rubella',
        'badge'     => 'badge-amber',
        'color'     => '#F59E0B',
        'gejala'    => ['Demam ringan 2-3 hari', 'Ruam merah muda menyebar cepat', 'Pembengkakan kelenjar getah bening', 'Nyeri sendi (dewasa)'],
        'penanganan'=> 'Istirahat dan cukup cairan. Vaksin MMR. Ibu hamil segera ke dokter.',
    ],
    'cacar'   => [
        'label'     => 'Cacar Air',
        'icon'      => '🟡',
        'class'     => 'cacar',
        'badge'     => 'badge-green',
        'color'     => '#10B981',
        'gejala'    => ['Demam ringan-sedang', 'Ruam berupa vesikel berisi cairan', 'Sangat gatal', 'Ruam muncul bertahap dari kepala ke badan'],
        'penanganan'=> 'Jaga kebersihan, jangan digaruk. Obat anti-gatal sesuai dokter. Vaksin Varisela.',
    ],
];

$info = $infoMap[$d['hasil']] ?? $infoMap['campak'];
$prob = $d['probabilitas'];

// Warna indikator konsistensi
$konsistensiColor = [
    'konsisten'       => ['bg' => '#ECFDF5', 'border' => '#A7F3D0', 'text' => '#065F46', 'icon' => 'ti-circle-check'],
    'mayoritas'       => ['bg' => '#FFFBEB', 'border' => '#FDE68A', 'text' => '#92400E', 'icon' => 'ti-alert-triangle'],
    'tidak_konsisten' => ['bg' => '#FEF2F2', 'border' => '#FECACA', 'text' => '#991B1B', 'icon' => 'ti-circle-x'],
];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hasil Diagnosis — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <style>
      .result-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 1.5rem;
        align-items: start;
      }
      .result-hero {
        display: flex;
        gap: 1.5rem;
        background: white;
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }
      .result-image-box {
        width: 250px;
        height: 250px;
        border-radius: var(--radius-md);
        background-color: var(--gray-100);
        /* Default rash image if none provided */
        background-image: url('https://images.unsplash.com/photo-1604164448130-d1df213c64eb?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80');
        background-size: cover;
        background-position: center;
        position: relative;
        flex-shrink: 0;
      }
      .result-image-box .badge-original {
        position: absolute;
        bottom: 12px;
        left: 12px;
        background: white;
        padding: 6px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
        color: var(--primary-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      
      .result-summary {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
      }
      .result-summary .top-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;
        color: var(--gray-500);
        margin-bottom: 12px;
      }
      .result-summary .top-meta .badge {
        background: var(--primary-color);
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 10px;
      }
      .result-summary h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 8px;
        line-height: 1.2;
      }
      .result-summary .confidence {
        font-size: 1.1rem;
        color: var(--gray-600);
        margin-bottom: 24px;
        display: flex;
        align-items: baseline;
        gap: 6px;
      }
      .result-summary .confidence strong {
        font-weight: 700;
        color: var(--text-primary);
        font-size: 1.25rem;
      }
      .consistency-alert {
        background: #f8fafc;
        border-radius: var(--radius-md);
        padding: 16px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
      }
      .consistency-alert.high {
        background: #f0fdfa;
      }
      .consistency-alert .icon-circle {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #0f3b99;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
      }
      .consistency-alert h4 {
        margin: 0 0 4px 0;
        font-size: 14px;
        color: var(--text-primary);
        font-weight: 600;
      }
      .consistency-alert p {
        margin: 0;
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.5;
      }
      
      .table-card, .info-disease-card {
        background: white;
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }
      
      .table-card h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        margin-bottom: 16px;
        color: var(--text-primary);
      }
      
      .comparison-table {
        width: 100%;
        border-collapse: collapse;
      }
      .comparison-table th {
        text-align: left;
        padding: 12px 16px;
        background: var(--gray-50);
        font-size: 12px;
        color: var(--gray-500);
        font-weight: 600;
      }
      .comparison-table td {
        padding: 16px;
        border-top: 1px solid var(--gray-100);
        font-size: 13px;
        color: var(--text-primary);
      }
      
      .analysis-cards-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
      }
      
      .analysis-mini-card {
        background: white;
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        padding: 1.5rem;
      }
      .analysis-mini-card h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        margin-bottom: 16px;
        color: var(--text-primary);
      }
      .bar-row {
        margin-bottom: 12px;
      }
      .bar-row:last-child {
        margin-bottom: 0;
      }
      .bar-label-group {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 6px;
        color: var(--gray-600);
      }
      .bar-label-group strong {
        color: var(--primary-color);
        font-weight: 700;
      }
      .bar-bg {
        width: 100%;
        height: 6px;
        background: var(--gray-100);
        border-radius: 99px;
        overflow: hidden;
      }
      .bar-fill {
        height: 100%;
        background: var(--primary-color);
        border-radius: 99px;
      }
      .bar-fill.gray {
        background: var(--gray-500);
      }
      
      .info-disease-card {
        background: #0b4bcc;
        color: white;
        border: none;
      }
      .info-disease-card h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        margin-bottom: 24px;
        color: white;
      }
      .info-section {
        background: rgba(255,255,255,0.1);
        border-radius: var(--radius-md);
        padding: 16px;
        margin-bottom: 16px;
      }
      .info-section h4 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        margin-bottom: 8px;
        color: rgba(255,255,255,0.8);
        font-weight: 500;
      }
      .info-section p {
        font-size: 13px;
        line-height: 1.5;
        margin: 0;
        color: white;
      }
      .info-section ul {
        margin: 0;
        padding-left: 0;
        list-style: none;
        font-size: 13px;
      }
      .info-section ul li {
        margin-bottom: 6px;
        padding-left: 16px;
        position: relative;
        line-height: 1.4;
      }
      .info-section ul li::before {
        content: "•";
        position: absolute;
        left: 0;
        color: rgba(255,255,255,0.6);
      }
      .info-disease-card .btn-white {
        background: white;
        color: #0b4bcc;
        width: 100%;
        padding: 12px;
        border: none;
        border-radius: var(--radius-md);
        font-weight: 600;
        cursor: pointer;
        display: block;
        text-align: center;
        text-decoration: none;
        margin-top: 16px;
      }
      
      .input-symptoms-card {
        background: white;
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        padding: 1.5rem;
      }
      .input-symptoms-card h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        margin-bottom: 16px;
        color: var(--text-primary);
      }
      .tags-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 24px;
      }
      .tag-pill {
        background: #e0e7ff;
        color: #3730a3;
        padding: 6px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .symptom-note {
        font-size: 12px;
        color: var(--gray-500);
        line-height: 1.5;
        padding-top: 16px;
        border-top: 1px solid var(--gray-100);
      }
    </style>
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
        
        <div class="result-hero">
          <div class="result-image-box" style="background-image: url('/user/image.php?f=<?= htmlspecialchars($d['foto_path']) ?>');">
            <div class="badge-original">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
              Original Scan
            </div>
          </div>
          
          <div class="result-summary">
            <div class="top-meta">
              <span class="badge">HASIL ANALISIS MEDIS</span>
              <span><?= date('d M Y • H:i A', strtotime($d['created_at'])) ?></span>
            </div>
            
            <h1><?= $info['label'] ?></h1>
            
            <div class="confidence">
              <strong><?= $triple ? $triple['fusion']['confidence'] : $d['confidence'] ?></strong>% <span>Confidence Level</span>
            </div>
            
            <?php
            $kStatus = $triple['konsistensi']['status'] ?? 'mayoritas';
            $kLabel = $triple['konsistensi']['label'] ?? 'Mayoritas Sepakat';
            $isHigh = ($kStatus === 'konsisten');
            ?>
            <div class="consistency-alert <?= $isHigh ? 'high' : '' ?>">
              <div class="icon-circle" style="<?= !$isHigh ? 'background:#F59E0B;' : '' ?>">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              </div>
              <div>
                <h4><?= $kLabel ?> <?= $isHigh ? '— Kepercayaan Tinggi' : '— Kepercayaan Menengah' ?></h4>
                <p>
                  <?php if ($isHigh): ?>
                  Kedua model AI memberikan hasil klasifikasi yang identik dengan skor probabilitas tinggi.
                  <?php else: ?>
                  Terdapat perbedaan kecil antara model visual dan gejala. Tetap ikuti saran dokter.
                  <?php endif; ?>
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="result-grid">
          <!-- Left Column -->
          <div>
            <?php if ($triple): ?>
            <div class="table-card">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                Perbandingan Hasil Analisis
              </h3>
              <table class="comparison-table">
                <thead>
                  <tr>
                    <th style="width: 50%;">Model Arsitektur</th>
                    <th>Prediksi Utama</th>
                    <th style="text-align:right;">Skor Akurasi</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <div style="display:flex; align-items:center; gap:10px; font-weight:500;">
                        <span style="background:#f1f5f9; padding:4px; border-radius:4px; display:inline-flex;">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#64748b;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                        </span>
                        Convolutional Neural Network (CNN)
                      </div>
                    </td>
                    <td><?= $infoMap[$triple['cnn']['prediksi']]['label'] ?? 'N/A' ?></td>
                    <td style="text-align:right; font-weight:700; color:var(--primary-color);"><?= $triple['cnn']['confidence'] ?>%</td>
                  </tr>
                  <tr>
                    <td>
                      <div style="display:flex; align-items:center; gap:10px; font-weight:500;">
                        <span style="background:#f1f5f9; padding:4px; border-radius:4px; display:inline-flex;">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#64748b;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        </span>
                        Multilayer Perceptron (MLP)
                      </div>
                    </td>
                    <td><?= $infoMap[$triple['mlp']['prediksi']]['label'] ?? 'N/A' ?></td>
                    <td style="text-align:right; font-weight:700; color:var(--primary-color);"><?= $triple['mlp']['confidence'] ?>%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <?php endif; ?>

            <div class="analysis-cards-row">
              <!-- Visual Analysis Bars -->
              <div class="analysis-mini-card">
                <h3>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                  Analisis Visual
                </h3>
                
                <?php
                $cnnProbs = $triple ? $triple['cnn']['probabilitas'] : $d['probabilitas'];
                foreach (['campak' => 'Campak', 'rubella' => 'Rubella', 'cacar' => 'Cacar Air'] as $key => $label):
                    $pct = $cnnProbs[$key] ?? 0;
                    $isTop = $pct >= max($cnnProbs);
                ?>
                <div class="bar-row">
                  <div class="bar-label-group">
                    <span><?= $label ?></span>
                    <strong <?= !$isTop ? 'style="color:var(--gray-600);"' : '' ?>><?= $pct ?>%</strong>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill <?= !$isTop ? 'gray' : '' ?>" style="width:<?= $pct ?>%;"></div>
                  </div>
                </div>
                <?php endforeach; ?>
              </div>

              <!-- Symptoms Analysis Bars -->
              <div class="analysis-mini-card">
                <h3>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
                  Analisis Gejala
                </h3>
                
                <?php
                $mlpProbs = $triple ? $triple['mlp']['probabilitas'] : $d['probabilitas'];
                foreach (['campak' => 'Campak', 'rubella' => 'Rubella', 'cacar' => 'Cacar Air'] as $key => $label):
                    $pct = $mlpProbs[$key] ?? 0;
                    $isTop = $pct >= max($mlpProbs);
                ?>
                <div class="bar-row">
                  <div class="bar-label-group">
                    <span><?= $label ?></span>
                    <strong <?= !$isTop ? 'style="color:var(--gray-600);"' : '' ?>><?= $pct ?>%</strong>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill <?= !$isTop ? 'gray' : '' ?>" style="width:<?= $pct ?>%;"></div>
                  </div>
                </div>
                <?php endforeach; ?>
              </div>
            </div>
          </div>

          <!-- Right Column -->
          <div>
            <!-- Info Penyakit -->
            <div class="info-disease-card">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                Informasi Penyakit
              </h3>
              
              <div class="info-section">
                <h4>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  Tentang
                </h4>
                <p>Infeksi virus menular yang menyebabkan ruam gatal seperti lepuh pada kulit dan gejala seperti flu.</p>
              </div>
              
              <div class="info-section">
                <h4>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                  Gejala Umum
                </h4>
                <ul>
                  <?php foreach ($info['gejala'] as $g): ?>
                  <li><?= $g ?></li>
                  <?php endforeach; ?>
                </ul>
              </div>
              
              <button class="btn-white" onclick="alert('<?= htmlspecialchars($info['penanganan']) ?>')">Panduan Perawatan</button>
            </div>
            
            <!-- Gejala yang Diinput -->
            <div class="input-symptoms-card">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Gejala yang Diinput
              </h3>
              
              <div class="tags-wrap">
                <?php
                $g = $d['gejala'];
                $symptomsList = [];
                if ($g['durasi_demam'] > 0 || ($g['demam_tinggi'] ?? 0)) $symptomsList[] = "Demam";
                if ($g['vesikel'] ?? 0) $symptomsList[] = "Muncul Bintik/Lenting";
                if ($g['batuk'] ?? 0) $symptomsList[] = "Batuk";
                if ($g['pilek'] ?? 0) $symptomsList[] = "Pilek";
                if ($g['sakit_tenggorokan'] ?? 0) $symptomsList[] = "Sakit Tenggorokan";
                if ($g['mata_merah'] ?? 0) $symptomsList[] = "Mata Merah";
                if ($g['nyeri_sendi'] ?? 0) $symptomsList[] = "Nyeri Sendi";
                if ($g['lemas'] ?? 0) $symptomsList[] = "Lemas/Sakit Kepala";
                if ($g['koplik_spot'] ?? 0) $symptomsList[] = "Bercak Putih di Mulut";
                if ($g['kelenjar_bengkak'] ?? 0) $symptomsList[] = "Kelenjar Bengkak";
                if ($g['hilang_nafsu_makan'] ?? 0) $symptomsList[] = "Nafsu Makan Turun";
                
                // fallback if empty
                if(empty($symptomsList)) $symptomsList[] = "Tidak ada gejala spesifik diinput";
                
                foreach ($symptomsList as $s):
                ?>
                <div class="tag-pill">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  <?= $s ?>
                </div>
                <?php endforeach; ?>
              </div>
              
              <div class="symptom-note">
                "Gejala mulai dirasakan sekitar <?= $g['durasi_demam'] ?? 0 ?> hari yang lalu berdasarkan input."
              </div>
            </div>
            
          </div>
        </div>
        
      </div>
    </main>
  </div>
</body>
</html>
