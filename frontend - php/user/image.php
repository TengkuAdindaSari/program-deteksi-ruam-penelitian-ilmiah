<?php
require_once '../includes/auth.php';
requireLogin();

$filename = $_GET['f'] ?? '';
if (empty($filename) || !preg_match('/^[a-zA-Z0-9_.-]+$/', $filename)) {
    exit('Invalid filename');
}

$uploadsDir = realpath(__DIR__ . '/../../flask-backend/uploads');
$path = realpath($uploadsDir . DIRECTORY_SEPARATOR . $filename);

if ($path && file_exists($path) && strpos($path, $uploadsDir) === 0) {
    $mime = mime_content_type($path);
    header("Content-Type: $mime");
    readfile($path);
} else {
    // Return a default image or 404
    header("HTTP/1.0 404 Not Found");
}
