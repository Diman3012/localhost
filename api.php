<?php
// api.php
include 'db.php';

header('Content-Type: application/json; charset=utf-8');

// Debug helper: ?debug=1 will return diagnostic information to help troubleshooting
if (isset($_GET['debug']) && $_GET['debug']) {
    try {
        $diag = [];
        $ver = $pdo->query("SELECT VERSION()")->fetchColumn();
        $diag['mysql_version'] = $ver;
        $diag['sql_mode'] = $pdo->query("SELECT @@session.sql_mode")->fetchColumn();
        // basic row counts
        $diag['counts'] = [
            'arrivals' => (int)$pdo->query("SELECT COUNT(*) FROM arrivals")->fetchColumn(),
            'packages' => (int)$pdo->query("SELECT COUNT(*) FROM packages")->fetchColumn(),
            'event_log' => (int)$pdo->query("SELECT COUNT(*) FROM event_log")->fetchColumn(),
            'statuses' => (int)$pdo->query("SELECT COUNT(*) FROM statuses")->fetchColumn()
        ];
        // sample a single arrival row
        $diag['sample_arrival'] = $pdo->query("SELECT * FROM arrivals LIMIT 1")->fetch(PDO::FETCH_ASSOC);
        echo json_encode(['debug' => $diag], JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
    } catch (\Exception $e) {
        http_response_code(500);
        echo json_encode(['error' => 'diag_failed', 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// Карта warehouse_id => id секции в фронтенде
$section_map = [
    1 => 'buffer',
    2 => 'south',
    3 => 'north',
    4 => 'ready'
];

$result = [];

try {
    foreach ($section_map as $warehouse_id => $section) {
        // 1) trucks: уникальные state_number у arrivals, которые ещё не уехали
        $stmt = $pdo->prepare("
            SELECT COUNT(DISTINCT state_number) AS cnt
            FROM arrivals
            WHERE warehouse_id = :wid
              AND (departed_at IS NULL OR departed_at = 'NULL')
        ");
        $stmt->execute([':wid' => $warehouse_id]);
        $trucks = (int) $stmt->fetchColumn();

        // 2) in: суммарно blocks_count по пакетам у arrivals этого склада, у которых статус = 'выгрузка' (завезено)
        $stmt = $pdo->prepare(
            "SELECT COALESCE(SUM(p.blocks_count),0) AS sum_blocks
             FROM packages p
             JOIN arrivals a ON p.arrival_id = a.id
             JOIN statuses s ON a.status_id = s.id
             WHERE a.warehouse_id = :wid AND s.name COLLATE utf8mb4_general_ci = 'выгрузка'"
        );
        $stmt->execute([':wid' => $warehouse_id]);
        $in = (int) $stmt->fetchColumn();

        // 3) out: суммарно blocks_count по пакетам у arrivals этого склада, у которых статус = 'загрузка' (вывезено)
        $stmt = $pdo->prepare(
            "SELECT COALESCE(SUM(p.blocks_count),0) AS sum_blocks
             FROM packages p
             JOIN arrivals a ON p.arrival_id = a.id
             JOIN statuses s ON a.status_id = s.id
             WHERE a.warehouse_id = :wid AND s.name COLLATE utf8mb4_general_ci = 'загрузка'"
        );
        $stmt->execute([':wid' => $warehouse_id]);
        $out = (int) $stmt->fetchColumn();

        // 4) последние 20 arrivals для этого склада
        $stmt = $pdo->prepare(
            "SELECT a.id, a.state_number, a.arrived_at, a.departed_at, a.camera_id, a.status_id, s.name AS status_name
             FROM arrivals a
             LEFT JOIN statuses s ON a.status_id = s.id
             WHERE a.warehouse_id = :wid
             ORDER BY a.arrived_at DESC
             LIMIT 20"
        );
        $stmt->execute([':wid' => $warehouse_id]);
        $arrivals_raw = $stmt->fetchAll();

        $arrivals = [];
        // подготовим несколько вспомогательных запросов
        // выбираем первую и последнюю фотографию для заезда (если есть)
        // Use != '' to avoid string 'NULL' or empty values; ensure ordering uses event_time
        $firstPhotoStmt = $pdo->prepare(
            "SELECT photo_path FROM event_log WHERE arrival_id = :aid AND photo_path != '' ORDER BY event_time ASC LIMIT 1"
        );
        $lastPhotoStmt = $pdo->prepare(
            "SELECT photo_path FROM event_log WHERE arrival_id = :aid AND photo_path != '' ORDER BY event_time DESC LIMIT 1"
        );
        $pkgCountStmt = $pdo->prepare("
            SELECT COUNT(*) AS cnt, COALESCE(SUM(blocks_count),0) AS blocks_sum
            FROM packages
            WHERE arrival_id = :aid
        ");

        foreach ($arrivals_raw as $a) {
            $aid = (int)$a['id'];

            // arrived_photo (первая имеющаяся фотография)
            $firstPhotoStmt->execute([':aid' => $aid]);
            $arrived_photo = $firstPhotoStmt->fetchColumn();
            if ($arrived_photo === false || $arrived_photo === '') $arrived_photo = null;

            // departed_photo (последняя имеющаяся фотография)
            $lastPhotoStmt->execute([':aid' => $aid]);
            $departed_photo = $lastPhotoStmt->fetchColumn();
            if ($departed_photo === false || $departed_photo === '') $departed_photo = null;

            // packages count and blocks sum
            $pkgCountStmt->execute([':aid' => $aid]);
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
                'packages_count' => $packages_count,   // пакетов (строк)
                'blocks_sum' => $blocks_sum           // анодов / блоков
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
