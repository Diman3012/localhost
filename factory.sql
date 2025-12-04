DROP DATABASE IF EXISTS factory;
CREATE DATABASE factory;
USE factory;

-- -----------------------------------------------------------
-- 1. Справочники
-- -----------------------------------------------------------

-- Номера машин
CREATE TABLE lgo_state_number (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Tiem_Data DATETIME NOT NULL,
    state_number VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Камеры (исправлено название таблицы - было camera, теперь cameras для согласованности)
CREATE TABLE cameras (
    id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    ip_camera VARCHAR(100) NOT NULL,
    type VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Учет машин
CREATE TABLE car_accounting (
    id INT PRIMARY KEY AUTO_INCREMENT,
    state_number VARCHAR(100),
    Tiem_Data DATETIME,
    photo_path VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Склады
CREATE TABLE warehouses (
    id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(100),
    account_camera INT UNSIGNED,
    camera_state_numbers INT UNSIGNED,
    FOREIGN KEY (account_camera) REFERENCES cameras (id),
    FOREIGN KEY (camera_state_numbers) REFERENCES cameras (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 2. Заезды 
-- -----------------------------------------------------------

CREATE TABLE arrivals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT UNSIGNED NOT NULL,  -- Изменено на UNSIGNED для согласованности
    state_number VARCHAR(100) NOT NULL,
    arrived_at DATETIME,
    departed_at DATETIME,
    camera_id INT UNSIGNED,
    status VARCHAR(100), -- простой или загружен
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)  -- Исправлено: camera → cameras
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- -----------------------------------------------------------
-- 3. Пакеты 
-- -----------------------------------------------------------

CREATE TABLE packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    arrival_id INT NOT NULL,
    blocks_count INT NOT NULL,
    defect_reason VARCHAR(255),
    FOREIGN KEY (arrival_id) REFERENCES arrivals(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 4. Фото и события 
-- -----------------------------------------------------------

CREATE TABLE event_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    arrival_id INT NOT NULL,
    event_time DATETIME,  -- Исправлено: NOW() → CURRENT_TIMESTAMP
    event_type VARCHAR(100),
    camera_id INT UNSIGNED,
    photo_path VARCHAR(255),
    FOREIGN KEY (arrival_id) REFERENCES arrivals(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;