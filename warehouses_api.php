<?php
// warehouses_api.php - API для управления складами
include 'db.php';
header('Content-Type: application/json; charset=utf-8');

try {
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        // Если передан warehouse_id, получить количество заездов для этого склада
        if (isset($_GET['warehouse_id'])) {
            $wid = (int)$_GET['warehouse_id'];
            $stmt = $pdo->prepare('SELECT COUNT(*) as cnt FROM arrivals WHERE warehouse_id = :wid');
            $stmt->execute([':wid' => $wid]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            $count = (int)$row['cnt'];
            echo json_encode(['arrivals_count' => $count], JSON_UNESCAPED_UNICODE);
            exit;
        }
        
        // Получить список всех складов
        $stmt = $pdo->query("SELECT id, name, type FROM warehouses ORDER BY id");
        $warehouses = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['warehouses' => $warehouses], JSON_UNESCAPED_UNICODE);
        exit;
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        // Чтение JSON тела запроса
        $body = file_get_contents('php://input');
        $data = json_decode($body, true);
        
        if (!is_array($data)) {
            http_response_code(400);
            echo json_encode(['error' => 'invalid_json'], JSON_UNESCAPED_UNICODE);
            exit;
        }

        // Добавление нового склада
        if (isset($data['action']) && $data['action'] === 'add') {
            $name = isset($data['name']) ? trim($data['name']) : null;
            $type = isset($data['type']) ? trim($data['type']) : null;

            if (!$name) {
                http_response_code(400);
                echo json_encode(['error' => 'name_required'], JSON_UNESCAPED_UNICODE);
                exit;
            }

            $stmt = $pdo->prepare('INSERT INTO warehouses (name, type) VALUES (:name, :type)');
            $stmt->execute([':name' => $name, ':type' => $type]);
            $newId = (int)$pdo->lastInsertId();
            echo json_encode(['ok' => true, 'id' => $newId, 'name' => $name, 'type' => $type], JSON_UNESCAPED_UNICODE);
            exit;
        }

        // Изменение названия/типа склада
        if (isset($data['action']) && $data['action'] === 'rename') {
            $id = isset($data['id']) ? (int)$data['id'] : null;
            $name = isset($data['name']) ? trim($data['name']) : null;
            $type = isset($data['type']) ? trim($data['type']) : null;

            if (!$id || !$name) {
                http_response_code(400);
                echo json_encode(['error' => 'id_and_name_required'], JSON_UNESCAPED_UNICODE);
                exit;
            }

            $updates = [];
            $params = [':id' => $id];
            $updates[] = 'name = :name';
            $params[':name'] = $name;
            if ($type !== null) {
                $updates[] = 'type = :type';
                $params[':type'] = $type;
            }

            $sql = 'UPDATE warehouses SET ' . implode(', ', $updates) . ' WHERE id = :id';
            $stmt = $pdo->prepare($sql);
            $stmt->execute($params);
            echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
            exit;
        }

        // Удаление склада
        if (isset($data['action']) && $data['action'] === 'delete') {
            $id = isset($data['id']) ? (int)$data['id'] : null;

            if (!$id) {
                http_response_code(400);
                echo json_encode(['error' => 'id_required'], JSON_UNESCAPED_UNICODE);
                exit;
            }

            // Проверяем, есть ли заезды для этого склада
            $stmt = $pdo->prepare('SELECT COUNT(*) as cnt FROM arrivals WHERE warehouse_id = :wid');
            $stmt->execute([':wid' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            $arrivals_count = (int)$row['cnt'];

            if ($arrivals_count > 0) {
                // Если есть заезды, требуем подтверждение
                $confirmation = isset($data['confirm']) ? (bool)$data['confirm'] : false;
                if (!$confirmation) {
                    http_response_code(409);
                    echo json_encode([
                        'error' => 'has_arrivals',
                        'arrivals_count' => $arrivals_count,
                        'message' => "В этом складе есть $arrivals_count заезд(ов). Введите название склада точно для подтверждения удаления."
                    ], JSON_UNESCAPED_UNICODE);
                    exit;
                }
            }

            // Удаляем склад
            $stmt = $pdo->prepare('DELETE FROM warehouses WHERE id = :id');
            $stmt->execute([':id' => $id]);
            echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
            exit;
        }

        http_response_code(400);
        echo json_encode(['error' => 'unknown_action'], JSON_UNESCAPED_UNICODE);
        exit;
    }

    http_response_code(405);
    echo json_encode(['error' => 'method_not_allowed'], JSON_UNESCAPED_UNICODE);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'internal', 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
}
?>
