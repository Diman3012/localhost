<?php
// cameras_api.php
include 'db.php';
header('Content-Type: application/json; charset=utf-8');

// Simple API for listing cameras for a given warehouse and updating camera records.
// GET params:
//  - warehouse_id: returns cameras linked to that warehouse (account_camera, camera_state_numbers)
//  - types=1 : returns camera_types list
// POST body (application/json) to update camera:
//  { id: <camera_id>, ip_camera: "...", camera_type_id: <id> }

try {
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        if (isset($_GET['types'])) {
            $stmt = $pdo->query("SELECT id, description FROM camera_types ORDER BY id");
            $types = $stmt->fetchAll();
            echo json_encode(['types' => $types], JSON_UNESCAPED_UNICODE);
            exit;
        }

        if (!isset($_GET['warehouse_id'])) {
            http_response_code(400);
            echo json_encode(['error' => 'warehouse_id_required']);
            exit;
        }

        $wid = (int)$_GET['warehouse_id'];
        // fetch warehouse cameras (account_camera and camera_state_numbers)
        $stmt = $pdo->prepare("SELECT account_camera, camera_state_numbers FROM warehouses WHERE id = :wid LIMIT 1");
        $stmt->execute([':wid' => $wid]);
        $row = $stmt->fetch();
        if (!$row) {
            http_response_code(404);
            echo json_encode(['error' => 'warehouse_not_found']);
            exit;
        }
        $ids = [];
        if (!empty($row['account_camera'])) $ids[] = (int)$row['account_camera'];
        if (!empty($row['camera_state_numbers'])) $ids[] = (int)$row['camera_state_numbers'];

        if (count($ids) === 0) {
            echo json_encode(['cameras' => []], JSON_UNESCAPED_UNICODE);
            exit;
        }

        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        $sql = "SELECT c.id, c.ip_camera, c.camera_type_id, ct.description AS camera_type_description
                FROM cameras c
                LEFT JOIN camera_types ct ON c.camera_type_id = ct.id
                WHERE c.id IN ($placeholders)";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($ids);
        $cameras = $stmt->fetchAll();
        echo json_encode(['cameras' => $cameras], JSON_UNESCAPED_UNICODE);
        exit;
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        // Read raw JSON body
        $body = file_get_contents('php://input');
        $data = json_decode($body, true);
        if (!is_array($data)) {
            http_response_code(400);
            echo json_encode(['error' => 'invalid_json']);
            exit;
        }
        $id = isset($data['id']) ? (int)$data['id'] : null;
        $ip = isset($data['ip_camera']) ? trim($data['ip_camera']) : null;
        $ctype = isset($data['camera_type_id']) ? ($data['camera_type_id'] !== '' ? (int)$data['camera_type_id'] : null) : null;

        // If request contains a type object -> create/update camera_types
        if (isset($data['type']) && is_array($data['type'])) {
            $t = $data['type'];
            $tid = isset($t['id']) && $t['id'] ? (int)$t['id'] : null;
            $desc = isset($t['description']) ? trim($t['description']) : null;
            if (!$desc) {
                http_response_code(400);
                echo json_encode(['error' => 'description_required']);
                exit;
            }
            if ($tid) {
                $stmt = $pdo->prepare('UPDATE camera_types SET description = :desc WHERE id = :id');
                $stmt->execute([':desc' => $desc, ':id' => $tid]);
                echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
                exit;
            } else {
                $stmt = $pdo->prepare('INSERT INTO camera_types (description) VALUES (:desc)');
                $stmt->execute([':desc' => $desc]);
                $newId = (int)$pdo->lastInsertId();
                echo json_encode(['ok' => true, 'id' => $newId], JSON_UNESCAPED_UNICODE);
                exit;
            }
        }

        if (!$id) {
            http_response_code(400);
            echo json_encode(['error' => 'id_required']);
            exit;
        }

        // Validate camera exists
        $stmt = $pdo->prepare("SELECT id FROM cameras WHERE id = :id");
        $stmt->execute([':id' => $id]);
        if (!$stmt->fetchColumn()) {
            http_response_code(404);
            echo json_encode(['error' => 'camera_not_found']);
            exit;
        }

        // Update fields
        $updates = [];
        $params = [':id' => $id];
        if ($ip !== null) { $updates[] = 'ip_camera = :ip'; $params[':ip'] = $ip; }
        if ($ctype !== null) { $updates[] = 'camera_type_id = :ctype'; $params[':ctype'] = $ctype; }

        if (count($updates) === 0) {
            echo json_encode(['ok' => true, 'message' => 'nothing_to_update'], JSON_UNESCAPED_UNICODE);
            exit;
        }

        $sql = 'UPDATE cameras SET ' . implode(', ', $updates) . ' WHERE id = :id';
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
        exit;
    }

    http_response_code(405);
    echo json_encode(['error' => 'method_not_allowed']);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'internal', 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
}
