<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
if (isAdmin()) { header('Location: /admin/dashboard.php'); exit; }

$user  = getUser();
$token = getToken();
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (empty($_FILES['foto']['tmp_name'])) {
        $error = 'Foto wajib diupload';
    } else {
        $data = [
            'durasi_demam'       => (int)($_POST['durasi_demam'] ?? 4),
            'demam_tinggi'       => isset($_POST['demam_tinggi'])       ? 1 : 0,
            'batuk'              => isset($_POST['batuk'])              ? 1 : 0,
            'pilek'              => isset($_POST['pilek'])              ? 1 : 0,
            'sakit_tenggorokan'  => isset($_POST['sakit_tenggorokan'])  ? 1 : 0,
            'mata_merah'         => isset($_POST['mata_merah'])         ? 1 : 0,
            'koplik_spot'        => isset($_POST['koplik_spot'])        ? 1 : 0,
            'kelenjar_bengkak'   => isset($_POST['kelenjar_bengkak'])   ? 1 : 0,
            'pola_ruam'          => isset($_POST['pola_ruam'])          ? 1 : 0,
            'nyeri_sendi'        => isset($_POST['nyeri_sendi'])        ? 1 : 0,
            'vesikel'            => isset($_POST['vesikel'])            ? 1 : 0,
            'hilang_nafsu_makan' => isset($_POST['hilang_nafsu_makan']) ? 1 : 0,
            'lemas'              => isset($_POST['lemas'])              ? 1 : 0,
        ];

        $res = Api::post('/diagnose/predict', $data, $token, ['foto' => $_FILES['foto']]);

        if ($res['success'] ?? false) {
            $id = $res['data']['id'];
            // Simpan triple result ke session untuk ditampilkan di halaman result
            $_SESSION['triple_result_' . $id] = $res['data']['triple'] ?? null;
            header("Location: /user/result.php?id=$id");
            exit;
        } else {
            $error = $res['message'] ?? 'Prediksi gagal, coba lagi';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnosis Baru - DermDetect Clinical Portal</title>
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
        <a href="/user/diagnose.php" class="nav-item active">
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
          <a href="/user/dashboard.php" class="topbar-link">Dashboard</a>
          <a href="/user/diagnose.php" class="topbar-link active">Diagnosis</a>
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
        
        <!-- Stepper -->
        <div class="stepper">
          <div class="step active">
            <div class="step-circle">1</div>
            <div class="step-label">Upload Foto</div>
          </div>
          <div class="step-line active"></div>
          <div class="step active">
            <div class="step-circle">2</div>
            <div class="step-label">Isi Gejala</div>
          </div>
          <div class="step-line"></div>
          <div class="step">
            <div class="step-circle">3</div>
            <div class="step-label">Hasil</div>
          </div>
        </div>
        
        <?php if ($error): ?>
        <div style="background-color: var(--warning-bg); color: var(--warning-text); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 2rem;">
            <?= htmlspecialchars($error) ?>
        </div>
        <?php endif; ?>

        <form method="POST" enctype="multipart/form-data">
          <div class="diagnosis-layout">
            
            <div class="diagnosis-main">
              <!-- Upload Card -->
              <div class="upload-card">
                <h3 class="card-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                  Upload Foto Ruam
                </h3>
                
                <div class="upload-area" onclick="document.getElementById('fotoInput').click();">
                  <div class="upload-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                  </div>
                  <p class="upload-text">Klik atau seret gambar ke sini</p>
                  <p class="upload-hint">Mendukung format JPG, PNG, atau WEBP (Maks. 5MB)</p>
                  
                  <input type="file" id="fotoInput" name="foto" accept="image/*" style="display:none;" onchange="previewFoto(this)" required>
                  <img id="previewImg" class="upload-preview" src="" alt="Preview" style="display:none; max-width: 100%; max-height: 200px; margin: 1rem auto; border-radius: var(--radius-md);">
                  <p id="namaFile" class="text-sm text-muted mt-1" style="font-size: 0.75rem; color: var(--text-secondary);"></p>
                  
                  <button type="button" class="btn-outline">Pilih File</button>
                </div>
              </div>

              <!-- Symptoms Card -->
              <div class="symptoms-card">
                <h3 class="card-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-color)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                  Gejala Klinis
                </h3>
                
                <div class="slider-group">
                  <div class="slider-header">
                    <span>Durasi Demam (Hari)</span>
                    <span class="slider-badge"><span id="durasiValBadge">3</span> Hari</span>
                  </div>
                  <div style="position: relative; margin-top: 1rem; margin-bottom: 0.5rem;">
                    <input type="range" name="durasi_demam" min="0" max="14" value="3" id="demamRange" oninput="document.getElementById('durasiValBadge').textContent=this.value">
                  </div>
                  <div class="slider-labels">
                    <span>0 HARI</span>
                    <span>7 HARI</span>
                    <span>14 HARI</span>
                  </div>
                </div>
                
                <div class="checkbox-grid">
                  <div class="checkbox-group">
                    <h4>GEJALA UMUM</h4>
                    <label class="checkbox-label">
                      <input type="checkbox" name="lemas" id="lemas">
                      Lemas (Malaise)
                    </label>
                    <label class="checkbox-label">
                      <input type="checkbox" name="demam_tinggi" id="demam_tinggi">
                      Demam Tinggi (>38.5°C)
                    </label>
                    <label class="checkbox-label">
                      <input type="checkbox" name="hilang_nafsu_makan" id="hilang_nafsu_makan">
                      Nafsu Makan Menurun
                    </label>
                  </div>
                  
                  <div class="checkbox-group">
                    <h4>PERNAFASAN & KEPALA</h4>
                    <label class="checkbox-label">
                      <input type="checkbox" name="batuk" id="batuk">
                      Batuk / Pilek
                    </label>
                    <label class="checkbox-label">
                      <input type="checkbox" name="pilek" id="pilek">
                      Hidung Tersumbat
                    </label>
                    <label class="checkbox-label">
                      <input type="checkbox" name="sakit_tenggorokan" id="sakit_tenggorokan">
                      Sakit Tenggorokan
                    </label>
                  </div>
                  
                  <div class="checkbox-group" style="grid-column: span 2;">
                    <h4>RUAM & GEJALA KHAS</h4>
                    <div class="checkbox-grid">
                      <div>
                        <label class="checkbox-label">
                          <input type="checkbox" name="pola_ruam" id="pola_ruam" checked>
                          Ruam Menyebar (Wajah ke Badan)
                        </label>
                        <label class="checkbox-label">
                          <input type="checkbox" name="mata_merah" id="mata_merah">
                          Mata Merah (Konjungtivitis)
                        </label>
                        <label class="checkbox-label">
                          <input type="checkbox" name="nyeri_sendi" id="nyeri_sendi">
                          Nyeri / Pegal Sendi
                        </label>
                      </div>
                      <div>
                        <label class="checkbox-label">
                          <input type="checkbox" name="kelenjar_bengkak" id="kelenjar_bengkak">
                          Pembengkakan Kelenjar (Leher)
                        </label>
                        <label class="checkbox-label">
                          <input type="checkbox" name="koplik_spot" id="koplik_spot">
                          Bintik putih di mulut (Koplik Spot)
                        </label>
                        <label class="checkbox-label">
                          <input type="checkbox" name="vesikel" id="vesikel">
                          Lenting Berisi Cairan (Vesikel)
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="action-bar">
                <button type="submit" class="btn-primary" style="padding: 1rem 2rem; font-size: 1rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg);">
                  Analisis Sekarang
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
                </button>
              </div>
            </div>
            
            <div class="diagnosis-sidebar">
              <div class="info-card">
                <h3 class="info-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                  Panduan Penggunaan
                </h3>
                <p class="info-desc">Pastikan analisis dilakukan dengan data yang akurat untuk hasil yang optimal.</p>
                <ul class="info-list">
                  <li>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:2px; color:#60a5fa"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    Gunakan pencahayaan yang terang saat memotret ruam.
                  </li>
                  <li>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:2px; color:#60a5fa"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    Pastikan area ruam terlihat fokus dan jelas.
                  </li>
                  <li>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:2px; color:#60a5fa"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    Lengkapi seluruh gejala yang dirasakan pasien.
                  </li>
                </ul>
              </div>
            </div>
            
          </div>
        </form>
        
      </div>
    </main>
  </div>

<script>
function previewFoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            const img = document.getElementById('previewImg');
            img.src = e.target.result;
            img.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
        document.getElementById('namaFile').textContent = input.files[0].name;
    }
}
</script>
</body>
</html>
