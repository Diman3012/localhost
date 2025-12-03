<?php
// api.php
include 'db.php';

header('Content-Type: application/json; charset=utf-8');

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

        // 2) in: суммарно blocks_count по пакетам, связанных с arrivals этого склада
        $stmt = $pdo->prepare("
            SELECT COALESCE(SUM(p.blocks_count),0) AS sum_blocks
            FROM packages p
            JOIN arrivals a ON p.arrival_id = a.id
            WHERE a.warehouse_id = :wid
        ");
        $stmt->execute([':wid' => $warehouse_id]);
        $in = (int) $stmt->fetchColumn();

        // 3) out: суммарно blocks_count по пакетам у arrivals с departed_at IS NOT NULL
        $stmt = $pdo->prepare("
            SELECT COALESCE(SUM(p.blocks_count),0) AS sum_blocks
            FROM packages p
            JOIN arrivals a ON p.arrival_id = a.id
            WHERE a.warehouse_id = :wid
              AND a.departed_at IS NOT NULL
              AND a.departed_at <> 'NULL'
        ");
        $stmt->execute([':wid' => $warehouse_id]);
        $out = (int) $stmt->fetchColumn();

        // 4) последние 20 arrivals для этого склада
        $stmt = $pdo->prepare("
            SELECT a.id, a.state_number, a.arrived_at, a.departed_at, a.camera_id
            FROM arrivals a
            WHERE a.warehouse_id = :wid
            ORDER BY a.arrived_at DESC
            LIMIT 20
        ");
        $stmt->execute([':wid' => $warehouse_id]);
        $arrivals_raw = $stmt->fetchAll();

        $arrivals = [];
        // подготовим несколько вспомогательных запросов
        $photoStmt = $pdo->prepare("
            SELECT photo_path
            FROM event_log
            WHERE arrival_id = :aid AND event_type = :etype
            ORDER BY event_time ASC
            LIMIT 1
        ");
        $pkgCountStmt = $pdo->prepare("
            SELECT COUNT(*) AS cnt, COALESCE(SUM(blocks_count),0) AS blocks_sum
            FROM packages
            WHERE arrival_id = :aid
        ");

        foreach ($arrivals_raw as $a) {
            $aid = (int)$a['id'];

            // arrived_photo
            $photoStmt->execute([':aid' => $aid, ':etype' => 'arrived_photo']);
            $arrived_photo = $photoStmt->fetchColumn();
            if ($arrived_photo === false) $arrived_photo = null;

            // departed_photo
            $photoStmt->execute([':aid' => $aid, ':etype' => 'departed_photo']);
            $departed_photo = $photoStmt->fetchColumn();
            if ($departed_photo === false) $departed_photo = null;

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
