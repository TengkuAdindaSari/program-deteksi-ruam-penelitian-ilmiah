<?php
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$user  = getUser();
$token = getToken();
$id    = (int)($_GET['id'] ?? 0);

if (!$id) {
    header('Location: /admin/diagnoses.php');
    exit;
}

$res = Api::get("/admin/diagnoses/$id", $token);
$d   = $res['data'] ?? null;

if (!$d) {
    flash('danger', 'Data diagnosis tidak ditemukan.');
    header('Location: /admin/diagnoses.php');
    exit;
}

$labelMap = ['campak'=>'Campak', 'rubella'=>'Rubella', 'cacar'=>'Cacar Air'];
$badgeMap = ['campak'=>'badge-blue', 'rubella'=>'badge-amber', 'cacar'=>'badge-green'];
$colorMap = ['campak'=>'#2563EB', 'rubella'=>'#F59E0B', 'cacar'=>'#10B981'];

$gejalaLabels = [
    'demam_tinggi'      => 'Demam Tinggi',
    'demam_ringan'      => 'Demam Ringan',
    'sakit_tenggorokan' => 'Sakit Tenggorokan',
    'mata_merah'        => 'Mata Merah',
    'koplik_spot'       => 'Koplik Spot',
    'kelenjar_bengkak'  => 'Kelenjar Bengkak',
    'nyeri_sendi'       => 'Nyeri Sendi',
    'vesikel'           => 'Vesikel',
    'lemas'             => 'Lemas',
];

$prob    = $d['probabilitas'] ?? [];
$gejala  = $d['gejala'] ?? [];
$triple  = $d['triple'] ?? null;
$flash   = getFlash();
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detail Diagnosis #<?= $d['id'] ?> — Admin DermDetect</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
        .detail-hero {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .detail-image {
            width: 220px;
            height: 220px;
            border-radius: var(--radius-lg);
            overflow: hidden;
            flex-shrink: 0;
            background: #f1f5f9;
            border: 1px solid var(--border-color);
        }
        .detail-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .detail-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .detail-info .result-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .detail-info .result-name {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        .detail-info .confidence-text {
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        .detail-info .confidence-text strong {
            font-size: 1.15rem;
            color: var(--text-primary);
        }
        .detail-meta {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }
        .detail-meta-item {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        .detail-meta-item .meta-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            font-weight: 700;
        }
        .detail-meta-item .meta-value {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .prob-section { margin-bottom: 1.5rem; }
        .prob-bar-row { margin-bottom: 0.85rem; }
        .prob-bar-row:last-child { margin-bottom: 0; }
        .prob-bar-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            margin-bottom: 0.35rem;
            color: var(--text-secondary);
        }
        .prob-bar-header strong {
            font-weight: 700;
            color: var(--text-primary);
        }
        .prob-bar-track {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 99px;
            overflow: hidden;
        }
        .prob-bar-fill {
            height: 100%;
            border-radius: 99px;
            transition: width 0.5s ease;
        }

        .gejala-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.6rem;
        }
        .gejala-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8125rem;
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-md);
            background: #f8fafc;
            border: 1px solid var(--border-color);
        }
        .gejala-item.active {
            background: #f0fdf4;
            border-color: #bbf7d0;
            color: #15803d;
        }
        .gejala-item.inactive {
            color: var(--text-secondary);
        }

        .triple-card {
            background: #fafbfd;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        .triple-card h4 {
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .triple-card p {
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .status-form {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex-wrap: wrap;
        }

        @media (max-width: 768px) {
            .detail-hero { flex-direction: column; }
            .detail-image { width: 100%; height: 200px; }
            .gejala-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

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
        <div class="sidebar">
            <div class="sidebar-header"><p>Panel Admin</p><h4><?= htmlspecialchars($user['nama']) ?></h4></div>
            <div class="sidebar-nav">
                <a href="/admin/dashboard.php"><i class="ti ti-layout-dashboard"></i> Dashboard</a>
                <a href="/admin/diagnoses.php" class="active"><i class="ti ti-history"></i> Histori Diagnosis</a>
                <a href="/admin/users.php"><i class="ti ti-users"></i> Kelola User</a>
                <a href="/admin/models.php"><i class="ti ti-cpu"></i> Kelola Model</a>

            </div>
        </div>

        <div>
            <!-- Breadcrumb -->
            <div style="margin-bottom:1rem;">
                <a href="/admin/diagnoses.php" style="font-size:0.8rem;color:var(--text-secondary);">
                    <i class="ti ti-arrow-left" style="font-size:14px;"></i> Kembali ke Histori
                </a>
            </div>

            <h2 class="page-title">Detail Diagnosis #<?= $d['id'] ?></h2>

            <?php if ($flash): ?>
            <div class="alert alert-<?= $flash['type']==='success'?'success':'danger' ?>">
                <?= htmlspecialchars($flash['message']) ?>
            </div>
            <?php endif; ?>

            <!-- Hero Section -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="detail-hero">
                        <div class="detail-image">
                            <?php
                            $fotoFile = basename($d['foto_path'] ?? '');
                            if ($fotoFile): ?>
                            <img src="/user/image.php?f=<?= urlencode($fotoFile) ?>"
                                 alt="Foto ruam" onerror="this.style.display='none'">
                            <?php else: ?>
                            <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:var(--text-secondary);">
                                <i class="ti ti-photo-off" style="font-size:48px;"></i>
                            </div>
                            <?php endif; ?>
                        </div>
                        <div class="detail-info">
                            <div class="result-label">Hasil Klasifikasi</div>
                            <div class="result-name" style="color:<?= $colorMap[$d['hasil']] ?? '#2563EB' ?>;">
                                <?= $labelMap[$d['hasil']] ?? $d['hasil'] ?>
                            </div>
                            <div class="confidence-text">
                                Tingkat keyakinan: <strong><?= $d['confidence'] ?>%</strong>
                            </div>
                            <div class="detail-meta">
                                <div class="detail-meta-item">
                                    <span class="meta-label">User</span>
                                    <span class="meta-value"><?= htmlspecialchars($d['user_nama'] ?? '-') ?></span>
                                </div>
                                <div class="detail-meta-item">
                                    <span class="meta-label">Tanggal</span>
                                    <span class="meta-value"><?= date('d M Y, H:i', strtotime($d['created_at'])) ?></span>
                                </div>
                                <div class="detail-meta-item">
                                    <span class="meta-label">Status</span>
                                    <span class="badge <?= $d['status']==='selesai'?'badge-green':($d['status']==='review'?'badge-amber':'badge-red') ?>">
                                        <?= ucfirst($d['status']) ?>
                                    </span>
                                </div>
                                <div class="detail-meta-item">
                                    <span class="meta-label">Model ID</span>
                                    <span class="meta-value"><?= $d['model_id'] ?? '-' ?></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid-2 mb-4">
                <!-- Probabilitas -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-chart-bar" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Probabilitas per Kelas</h3>
                    </div>
                    <div class="card-body">
                        <?php
                        $probBars = [
                            ['label'=>'Campak',    'val'=>$prob['campak']  ?? 0, 'color'=>'#2563EB'],
                            ['label'=>'Rubella',   'val'=>$prob['rubella'] ?? 0, 'color'=>'#F59E0B'],
                            ['label'=>'Cacar Air', 'val'=>$prob['cacar']   ?? 0, 'color'=>'#10B981'],
                        ];
                        foreach ($probBars as $pb):
                        ?>
                        <div class="prob-bar-row">
                            <div class="prob-bar-header">
                                <span><?= $pb['label'] ?></span>
                                <strong><?= $pb['val'] ?>%</strong>
                            </div>
                            <div class="prob-bar-track">
                                <div class="prob-bar-fill" style="width:<?= $pb['val'] ?>%;background:<?= $pb['color'] ?>;"></div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>

                <!-- Gejala -->
                <div class="card">
                    <div class="card-header">
                        <i class="ti ti-stethoscope" style="color:#2563EB;font-size:18px;"></i>
                        <h3>Gejala yang Dilaporkan</h3>
                    </div>
                    <div class="card-body">
                        <div class="gejala-grid">
                            <?php
                            foreach ($gejalaLabels as $key => $label):
                                if ($key === 'durasi_demam') continue;
                                $isActive = !empty($gejala[$key]);
                            ?>
                            <div class="gejala-item <?= $isActive ? 'active' : 'inactive' ?>">
                                <i class="ti ti-<?= $isActive ? 'circle-check' : 'circle-x' ?>"
                                   style="font-size:16px;<?= $isActive ? 'color:#16a34a;' : 'color:#94a3b8;' ?>"></i>
                                <?= $label ?>
                            </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Triple Validation -->
            <?php if ($triple): ?>
            <div class="card mb-4">
                <div class="card-header">
                    <i class="ti ti-checklist" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Validasi Triple (CNN + Gejala + Aturan)</h3>
                    <?php
                    $konsistensi = $triple['konsistensi'] ?? 'tidak_konsisten';
                    $konsBadge = [
                        'konsisten'       => 'badge-green',
                        'mayoritas'       => 'badge-amber',
                        'tidak_konsisten' => 'badge-red',
                    ];
                    ?>
                    <span class="badge <?= $konsBadge[$konsistensi] ?? 'badge-gray' ?> ml-auto">
                        <?= ucfirst(str_replace('_', ' ', $konsistensi)) ?>
                    </span>
                </div>
                <div class="card-body">
                    <?php if (!empty($triple['hasil_cnn'])): ?>
                    <div class="triple-card">
                        <h4><i class="ti ti-brain" style="color:#2563EB;"></i> CNN (Model AI)</h4>
                        <p>Hasil: <strong><?= $labelMap[$triple['hasil_cnn']] ?? $triple['hasil_cnn'] ?></strong></p>
                    </div>
                    <?php endif; ?>
                    <?php if (!empty($triple['hasil_gejala'])): ?>
                    <div class="triple-card">
                        <h4><i class="ti ti-stethoscope" style="color:#F59E0B;"></i> Analisis Gejala</h4>
                        <p>Hasil: <strong><?= $labelMap[$triple['hasil_gejala']] ?? $triple['hasil_gejala'] ?></strong></p>
                    </div>
                    <?php endif; ?>
                    <?php if (!empty($triple['hasil_aturan'])): ?>
                    <div class="triple-card">
                        <h4><i class="ti ti-book" style="color:#10B981;"></i> Sistem Aturan</h4>
                        <p>Hasil: <strong><?= $labelMap[$triple['hasil_aturan']] ?? $triple['hasil_aturan'] ?></strong></p>
                    </div>
                    <?php endif; ?>
                    <?php if (!empty($triple['penjelasan'])): ?>
                    <div style="margin-top:0.75rem;padding:0.75rem;background:#f0f5ff;border-radius:var(--radius-md);font-size:0.8125rem;color:var(--text-secondary);line-height:1.6;">
                        <i class="ti ti-info-circle" style="color:var(--primary-color);"></i>
                        <?= htmlspecialchars($triple['penjelasan']) ?>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            <?php endif; ?>

            <!-- Aksi Admin -->
            <div class="card">
                <div class="card-header">
                    <i class="ti ti-settings" style="color:#2563EB;font-size:18px;"></i>
                    <h3>Aksi Admin</h3>
                </div>
                <div class="card-body">
                    <div class="status-form">
                        <span class="text-sm" style="font-weight:600;margin-right:0.5rem;">Ubah Status:</span>
                        <?php
                        $statuses = ['selesai' => 'Selesai', 'review' => 'Review', 'dihapus' => 'Dihapus'];
                        foreach ($statuses as $sKey => $sLabel):
                            $isCurrentStatus = ($d['status'] === $sKey);
                        ?>
                        <form method="POST" action="/admin/diagnosis-action.php" style="display:inline;">
                            <input type="hidden" name="id" value="<?= $d['id'] ?>">
                            <input type="hidden" name="action" value="status">
                            <input type="hidden" name="status" value="<?= $sKey ?>">
                            <button type="submit" class="btn <?= $isCurrentStatus ? 'btn-primary' : 'btn-secondary' ?> btn-sm"
                                    <?= $isCurrentStatus ? 'disabled style="opacity:0.6;cursor:default;"' : '' ?>>
                                <?= $sLabel ?>
                            </button>
                        </form>
                        <?php endforeach; ?>

                        <div style="margin-left:auto;">
                            <form method="POST" action="/admin/diagnosis-action.php"
                                  onsubmit="return confirm('Yakin hapus diagnosis ini secara permanen?')">
                                <input type="hidden" name="id" value="<?= $d['id'] ?>">
                                <input type="hidden" name="action" value="delete">
                                <button type="submit" class="btn btn-danger btn-sm">
                                    <i class="ti ti-trash"></i> Hapus Permanen
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
