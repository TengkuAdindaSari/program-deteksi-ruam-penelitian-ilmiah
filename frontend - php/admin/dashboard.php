<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$user  = getUser();
$token = getToken();
$res   = Api::get('/admin/dashboard', $token);
$data  = $res['data'] ?? [];
$dist  = $data['distribusi'] ?? [];
$tren  = $data['tren_7_hari'] ?? [];
$model = $data['model_aktif'] ?? null;
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Admin — DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
</head>
<body>

<!-- Navbar Admin -->
<nav class="navbar" style="border-bottom-color:#FECACA;">
    <div class="navbar-brand" style="color:#DC2626;">
        <i class="ti ti-shield-check"></i> DermDetect Admin
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:8px;">
        <span class="badge badge-red">Administrator</span>
        <div class="nav-avatar" style="background:#FEF2F2;color:#DC2626;">
            <?= strtoupper(substr($user['nama'], 0, 2)) ?>
        </div>
        <a href="/logout.php" class="btn btn-secondary btn-sm">
            <i class="ti ti-logout"></i> Keluar
        </a>
    </div>
</nav>

<div class="container">
    <div class="admin-layout">

        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <p>Panel Admin</p>
                <h4><?= htmlspecialchars($user['nama']) ?></h4>
            </div>
            <div class="sidebar-nav">
                <a href="/admin/dashboard.php" class="active">
                    <i class="ti ti-layout-dashboard"></i> Dashboard
                </a>
                <a href="/admin/diagnoses.php">
                    <i class="ti ti-history"></i> Histori Diagnosis
                </a>
                <a href="/admin/users.php">
                    <i class="ti ti-users"></i> Kelola User
                </a>
                <a href="/admin/models.php">
                    <i class="ti ti-cpu"></i> Kelola Model
                </a>

            </div>
        </div>

        <!-- Konten -->
        <div>
            <h2 class="page-title">Dashboard</h2>

            <!-- Metrik -->
            <div class="metrics-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 1.5rem;">
                <div class="metric-card" style="border-top: 3px solid #2563EB;">
                    <div class="metric-label" style="color:#2563EB;">Total Campak</div>
                    <div class="metric-value" style="color:#2563EB;"><?= number_format($dist['campak'] ?? 0) ?></div>
                </div>
                <div class="metric-card" style="border-top: 3px solid #F59E0B;">
                    <div class="metric-label" style="color:#B45309;">Total Rubella</div>
                    <div class="metric-value" style="color:#F59E0B;"><?= number_format($dist['rubella'] ?? 0) ?></div>
                </div>
                <div class="metric-card" style="border-top: 3px solid #10B981;">
                    <div class="metric-label" style="color:#059669;">Total Cacar Air</div>
                    <div class="metric-value" style="color:#10B981;"><?= number_format($dist['cacar'] ?? 0) ?></div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Total User</div>
                    <div class="metric-value"><?= number_format($data['total_user'] ?? 0) ?></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Perlu Review</div>
                    <div class="metric-value" style="color:#F59E0B;"><?= $data['review_pending'] ?? 0 ?></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Akurasi Model</div>
                    <div class="metric-value" style="color:#10B981;">
                        <?= $model ? round($model['akurasi'] * 100, 1) . '%' : '-' ?>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <!-- Distribusi -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-chart-pie" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Distribusi Hasil Diagnosis</h3>
                    </div>
                    <div class="card-body">
                        <?php
                        $total = ($dist['campak']??0) + ($dist['rubella']??0) + ($dist['cacar']??0);
                        $bars  = [
                            ['label'=>'Campak',   'val'=>$dist['campak']??0,  'color'=>'#2563EB'],
                            ['label'=>'Rubella',  'val'=>$dist['rubella']??0, 'color'=>'#F59E0B'],
                            ['label'=>'Cacar Air','val'=>$dist['cacar']??0,   'color'=>'#10B981'],
                        ];
                        foreach ($bars as $b):
                            $pct = $total > 0 ? round($b['val']/$total*100) : 0;
                        ?>
                        <div style="margin-bottom:12px;">
                            <div class="flex items-center gap-2 mb-1">
                                <span style="font-size:13px;font-weight:500;"><?= $b['label'] ?></span>
                                <span class="text-muted text-sm ml-auto"><?= $b['val'] ?> (<?= $pct ?>%)</span>
                            </div>
                            <div class="progress-track" style="height:10px;">
                                <div class="progress-fill" style="width:<?= $pct ?>%;background:<?= $b['color'] ?>;"></div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>

                <!-- Model Aktif -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-cpu" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Model Aktif</h3>
                        <span class="badge badge-green ml-auto">Aktif</span>
                    </div>
                    <div class="card-body">
                        <?php if ($model): ?>
                        <div style="margin-bottom:12px;">
                            <div style="font-size:15px;font-weight:600;margin-bottom:8px;"><?= htmlspecialchars($model['nama_file']) ?></div>
                            <div class="flex gap-3">
                                <div>
                                    <div class="metric-label">Versi</div>
                                    <div style="font-weight:600;"><?= $model['versi'] ?></div>
                                </div>
                                <div>
                                    <div class="metric-label">Akurasi</div>
                                    <div style="font-weight:600;color:#10B981;"><?= round($model['akurasi']*100,1) ?>%</div>
                                </div>
                                <div>
                                    <div class="metric-label">F1-Score</div>
                                    <div style="font-weight:600;"><?= $model['f1_score'] ?></div>
                                </div>
                            </div>
                        </div>
                        <?php else: ?>
                        <p class="text-muted">Tidak ada model aktif.</p>
                        <?php endif; ?>
                        <hr class="divider">
                        <a href="/admin/models.php" class="btn btn-secondary btn-block">
                            <i class="ti ti-settings"></i> Kelola Model
                        </a>
                    </div>
                </div>
            </div>

            <!-- Tren 7 hari -->
            <div class="card mt-4">
                <div class="card-header">
                    <i class="ti ti-trending-up" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Tren Diagnosis 7 Hari Terakhir</h3>
                </div>
                <div class="card-body">
                    <?php
                    $maxTren = max(array_column($tren, 'jumlah') ?: [1]);
                    ?>
                    <div style="display:flex;align-items:flex-end;gap:8px;height:80px;">
                        <?php foreach ($tren as $t):
                            $h = $maxTren > 0 ? round($t['jumlah']/$maxTren*70) : 0;
                        ?>
                        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;">
                            <span style="font-size:10px;color:#6B7280;"><?= $t['jumlah'] ?></span>
                            <div style="width:100%;height:<?= max($h,2) ?>px;background:#2563EB;border-radius:3px 3px 0 0;"></div>
                            <span style="font-size:10px;color:#9CA3AF;"><?= date('d/m', strtotime($t['tanggal'])) ?></span>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
