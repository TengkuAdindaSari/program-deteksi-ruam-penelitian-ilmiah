<?php
/**
 * includes/api.php
 * Helper untuk memanggil Flask API dari PHP menggunakan cURL
 */

define('API_URL', 'http://127.0.0.1:5000/api');

class Api {

    /**
     * Kirim request ke Flask API
     */
    public static function request($method, $endpoint, $data = [], $token = null, $files = null) {
        $url = API_URL . $endpoint;
        $ch  = curl_init($url);

        $headers = ['Accept: application/json'];
        if ($token) {
            $headers[] = 'Authorization: Bearer ' . $token;
        }

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);

        if ($method === 'POST' || $method === 'PUT') {
            if ($files) {
                // Multipart form-data (upload file)
                $postData = $data;
                foreach ($files as $key => $file) {
                    $postData[$key] = new CURLFile(
                        $file['tmp_name'],
                        $file['type'],
                        $file['name']
                    );
                }
                curl_setopt($ch, CURLOPT_POST, true);
                curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
            } else {
                // JSON body
                $headers[]  = 'Content-Type: application/json';
                curl_setopt($ch, CURLOPT_POST, true);
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
            if ($method === 'PUT') {
                curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
            }
        } elseif ($method === 'DELETE') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error    = curl_error($ch);
        curl_close($ch);

        if ($error) {
            return ['success' => false, 'message' => 'Tidak dapat terhubung ke server: ' . $error];
        }

        $decoded = json_decode($response, true);
        return $decoded ?? ['success' => false, 'message' => 'Response tidak valid'];
    }

    public static function get($endpoint, $token = null) {
        return self::request('GET', $endpoint, [], $token);
    }

    public static function post($endpoint, $data = [], $token = null, $files = null) {
        return self::request('POST', $endpoint, $data, $token, $files);
    }

    public static function put($endpoint, $data = [], $token = null) {
        return self::request('PUT', $endpoint, $data, $token);
    }

    public static function delete($endpoint, $token = null) {
        return self::request('DELETE', $endpoint, [], $token);
    }
}
