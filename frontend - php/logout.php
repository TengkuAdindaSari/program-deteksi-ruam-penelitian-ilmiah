<?php
require_once 'includes/auth.php';
require_once 'includes/api.php';

if (isLoggedIn()) {
    Api::post('/auth/logout', [], getToken());
    destroySession();
}

header('Location: /login.php');
exit;
