<?php
// db.php
$host = '127.0.0.1';
$db   = 'factory';       // имя вашей БД из XML
$user = 'root';
$pass = '';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";

$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
    // Ensure connection uses utf8mb4 and predictable session settings for newer MySQL
    // This keeps behavior consistent across MySQL versions (5.5 -> 8.x)
    // Disable strict ONLY_FULL_GROUP_BY style modes for compatibility with legacy queries
    try {
        $pdo->exec("SET NAMES 'utf8mb4'");
        // clear sql_mode to avoid ONLY_FULL_GROUP_BY and other strict modes that differ between versions
        $pdo->exec("SET SESSION sql_mode = ''");
        // ensure timezone is session-local (optional)
        $pdo->exec("SET time_zone = @@global.time_zone");
    } catch (\Exception $e) {
        // non-fatal: if server doesn't allow changing session variables, ignore
    }
} catch (\PDOException $e) {
    // Если подключение не удалось — вернём json-ошибку и остановим выполнение.
    header('Content-Type: application/json; charset=utf-8');
    http_response_code(500);
    echo json_encode([
        'error' => 'Ошибка подключения к базе данных',
        'message' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
    exit;
}
