<?php
/**
 * includes/auth.php
 * Manajemen session dan autentikasi
 */

// Fix session persistence untuk PHP built-in server
$sessionPath = sys_get_temp_dir() . '/dermdetect_sessions';
if (!is_dir($sessionPath)) { mkdir($sessionPath, 0777, true); }
session_save_path($sessionPath);
ini_set('session.gc_maxlifetime', 86400);
ini_set('session.cookie_lifetime', 86400);
session_start();

function isLoggedIn() {
    return isset($_SESSION['token']) && isset($_SESSION['user']);
}

function isAdmin() {
    return isLoggedIn() && $_SESSION['user']['role'] === 'admin';
}

function getToken() {
    return $_SESSION['token'] ?? null;
}

function getUser() {
    return $_SESSION['user'] ?? null;
}

function requireLogin() {
    if (!isLoggedIn()) {
        header('Location: /login.php');
        exit;
    }
}

function requireAdmin() {
    if (!isAdmin()) {
        header('Location: /user/dashboard.php');
        exit;
    }
}

function requireGuest() {
    if (isLoggedIn()) {
        if (isAdmin()) {
            header('Location: /admin/dashboard.php');
        } else {
            header('Location: /user/dashboard.php');
        }
        exit;
    }
}

function setSession($token, $user) {
    $_SESSION['token'] = $token;
    $_SESSION['user']  = $user;
}

function destroySession() {
    session_destroy();
}

function flash($type, $message) {
    $_SESSION['flash'] = ['type' => $type, 'message' => $message];
}

function getFlash() {
    if (isset($_SESSION['flash'])) {
        $flash = $_SESSION['flash'];
        unset($_SESSION['flash']);
        return $flash;
    }
    return null;
}
