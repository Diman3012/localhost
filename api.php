<?php
// api.php - Warehouse monitoring API for MySQL 8.0+
include 'db.php';

header('Content-Type: application/json; charset=utf-8');

// Debug helper: ?debug=1 returns diagnostic information
if (isset($_GET['debug']) && $_GET['debug']) {
    try {
        $diag = [];
        $diag['mysql_version'] = $pdo->query("SELECT VERSION()")->fetchColumn();
        $diag['sql_mode'] = $pdo->query("SELECT @@session.sql_mode")->fetchColumn();
        $diag['counts'] = [
            'arrivals' => (int)$pdo->query("SELECT COUNT(*) FROM arrivals")->fetchColumn(),
            'packages' => (int)$pdo->query("SELECT COUNT(*) FROM packages")->fetchColumn(),
            'event_log' => (int)$pdo->query("SELECT COUNT(*) FROM event_log")->fetchColumn(),
            'statuses' => (int)$pdo->query("SELECT COUNT(*) FROM statuses")->fetchColumn()
        ];
        $diag['sample_arrival'] = $pdo->query("SELECT * FROM arrivals LIMIT 1")->fetch(PDO::FETCH_ASSOC);
        echo json_encode(['debug' => $diag], JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
    } catch (\Exception $e) {
        http_response_code(500);
        echo json_encode(['error' => 'diag_failed', 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// Warehouse to section mapping
$section_map = [
    1 => 'buffer',
    2 => 'south',
    3 => 'north',
    4 => 'ready'
];

$result = [];
$verboseDebug = (isset($_GET['debug']) && $_GET['debug'] == 2);

function safeExecute($stmt, $params, $sql = null) {
    global $verboseDebug;
    try {
        $stmt->execute($params);
        return true;
    } catch (\Exception $e) {
        if ($verboseDebug) {
            http_response_code(500);
            echo json_encode([
                'error' => 'query_failed',
                'message' => $e->getMessage(),
                'sql' => $sql,
                'params' => $params
            ], JSON_UNESCAPED_UNICODE);
            exit;
        }
        throw $e;
    }
}

try {
    foreach ($section_map as $warehouse_id => $section) {
        // 1) Count of unique trucks (arrivals not departed yet)
        $sql = "SELECT COUNT(DISTINCT state_number) AS cnt
                FROM arrivals
                WHERE warehouse_id = :wid AND departed_at IS NULL";
        $stmt = $pdo->prepare($sql);
        safeExecute($stmt, [':wid' => $warehouse_id], $sql);
        $trucks = (int) $stmt->fetchColumn();

        // 2) Total blocks count for "выгрузка" status (loaded/received)
        $sql = "SELECT COALESCE(SUM(p.blocks_count), 0) AS sum_blocks
                FROM packages p
                JOIN arrivals a ON p.arrival_id = a.id
                JOIN statuses s ON a.status_id = s.id
                WHERE a.warehouse_id = :wid AND s.name = 'выгрузка'";
        $stmt = $pdo->prepare($sql);
        safeExecute($stmt, [':wid' => $warehouse_id], $sql);
        $in = (int) $stmt->fetchColumn();

        // 3) Total blocks count for "загрузка" status (shipped/sent)
        $sql = "SELECT COALESCE(SUM(p.blocks_count), 0) AS sum_blocks
                FROM packages p
                JOIN arrivals a ON p.arrival_id = a.id
                JOIN statuses s ON a.status_id = s.id
                WHERE a.warehouse_id = :wid AND s.name = 'загрузка'";
        $stmt = $pdo->prepare($sql);
        safeExecute($stmt, [':wid' => $warehouse_id], $sql);
        $out = (int) $stmt->fetchColumn();

        // 4) Last 20 arrivals for this warehouse
        $sql = "SELECT a.id, a.state_number, a.arrived_at, a.departed_at,
                       a.camera_id, a.status_id, s.name AS status_name
                FROM arrivals a
                LEFT JOIN statuses s ON a.status_id = s.id
                WHERE a.warehouse_id = :wid
                ORDER BY a.arrived_at DESC
                LIMIT 20";
        $stmt = $pdo->prepare($sql);
        safeExecute($stmt, [':wid' => $warehouse_id], $sql);
        $arrivals_raw = $stmt->fetchAll();

        // Prepare statements for photo and package queries
        $sqlFirstPhoto = "SELECT photo_path FROM event_log 
                         WHERE arrival_id = :aid AND photo_path IS NOT NULL AND photo_path != '' 
                         ORDER BY event_time ASC LIMIT 1";
        $sqlLastPhoto = "SELECT photo_path FROM event_log 
                        WHERE arrival_id = :aid AND photo_path IS NOT NULL AND photo_path != '' 
                        ORDER BY event_time DESC LIMIT 1";
        $sqlPkg = "SELECT COUNT(*) AS cnt, COALESCE(SUM(blocks_count), 0) AS blocks_sum 
                   FROM packages WHERE arrival_id = :aid";
        
        $firstPhotoStmt = $pdo->prepare($sqlFirstPhoto);
        $lastPhotoStmt = $pdo->prepare($sqlLastPhoto);
        $pkgCountStmt = $pdo->prepare($sqlPkg);

        $arrivals = [];
        foreach ($arrivals_raw as $a) {
            $aid = (int)$a['id'];

            // Get first photo
            safeExecute($firstPhotoStmt, [':aid' => $aid], $sqlFirstPhoto);
            $arrived_photo = $firstPhotoStmt->fetchColumn();
            $arrived_photo = ($arrived_photo === false || $arrived_photo === null) ? null : (string)$arrived_photo;

            // Get last photo
            safeExecute($lastPhotoStmt, [':aid' => $aid], $sqlLastPhoto);
            $departed_photo = $lastPhotoStmt->fetchColumn();
            $departed_photo = ($departed_photo === false || $departed_photo === null) ? null : (string)$departed_photo;

            // Get package info
            safeExecute($pkgCountStmt, [':aid' => $aid], $sqlPkg);
            $pkgInfo = $pkgCountStmt->fetch();
            $packages_count = (int)($pkgInfo['cnt'] ?? 0);
            $blocks_sum = (int)($pkgInfo['blocks_sum'] ?? 0);

            $arrivals[] = [
                'id' => $aid,
                'state_number' => $a['state_number'],
                'arrived_at' => $a['arrived_at'],
                'departed_at' => $a['departed_at'],
                'status_id' => isset($a['status_id']) ? (int)$a['status_id'] : null,
                'status_name' => $a['status_name'] ?? null,
                'arrived_photo' => $arrived_photo,
                'departed_photo' => $departed_photo,
                'packages_count' => $packages_count,
                'blocks_sum' => $blocks_sum
            ];
        }

        $result[$section] = [
            'trucks' => $trucks,
            'in' => $in,
            'out' => $out,
            'arrivals' => $arrivals
        ];
    }

    echo json_encode($result, JSON_UNESCAPED_UNICODE);

} catch (\Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'internal_error', 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
}
