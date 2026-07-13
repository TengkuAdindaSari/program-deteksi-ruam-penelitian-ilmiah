<?php
/**
 * diagnosis-action.php
 * Handles admin actions on diagnoses: delete, update status
 */
require_once '../includes/auth.php';
require_once '../includes/api.php';
requireLogin();
requireAdmin();

$token  = getToken();
$id     = (int)($_POST['id'] ?? 0);
$action = $_POST['action'] ?? '';

if (!$id) {
    flash('danger', 'ID diagnosis tidak valid.');
    header('Location: /admin/diagnoses.php');
    exit;
}

switch ($action) {
    case 'delete':
        $res = Api::delete("/admin/diagnoses/$id", $token);
        if ($res['success'] ?? false) {
            flash('success', 'Diagnosis berhasil dihapus.');
        } else {
            flash('danger', $res['message'] ?? 'Gagal menghapus diagnosis.');
        }
        header('Location: /admin/diagnoses.php');
        exit;

    case 'status':
        $status = $_POST['status'] ?? '';
        $allowed = ['selesai', 'review', 'dihapus'];
        if (!in_array($status, $allowed)) {
            flash('danger', 'Status tidak valid.');
            header("Location: /admin/diagnosis-detail.php?id=$id");
            exit;
        }
        $res = Api::put("/admin/diagnoses/$id/status", ['status' => $status], $token);
        if ($res['success'] ?? false) {
            flash('success', "Status berhasil diubah ke '$status'.");
        } else {
            flash('danger', $res['message'] ?? 'Gagal mengubah status.');
        }
        header("Location: /admin/diagnosis-detail.php?id=$id");
        exit;

    default:
        flash('danger', 'Aksi tidak dikenali.');
        header('Location: /admin/diagnoses.php');
        exit;
}
