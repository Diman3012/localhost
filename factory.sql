CREATE DATABASE factory;
USE factory;

-- -----------------------------------------------------------
-- 1. Справочники
-- -----------------------------------------------------------

-- Номера машин
CREATE TABLE lgo_state_number (
    id INT AUTO_INCREMENT,
    Tiem_Data DATETIME NOT NULL,
    state_number VARCHAR(100) NOT NULL,
    
    PRIMARY KEY (state_number, Tiem_Data),  -- ключ составной
    UNIQUE (id)
);

-- Камеры
CREATE TABLE cameras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_camera VARCHAR(100) NOT NULL
);

-- Учет машин
CREATE TABLE car_accounting (
    id INT PRIMARY KEY AUTO_INCREMENT,
    state_number VARCHAR(100),
    Tiem_Data DATETIME,

    FOREIGN KEY (state_number, Tiem_Data)
        REFERENCES lgo_state_number(state_number, Tiem_Data)
);

-- Склады
CREATE TABLE warehouses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(100)
);

-- -----------------------------------------------------------
-- 2. Заезды 
-- -----------------------------------------------------------

CREATE TABLE arrivals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT NOT NULL,
    state_number VARCHAR(100) NOT NULL,
    arrived_at DATETIME,
    departed_at DATETIME,
    camera_id INT,
    status VARCHAR(100),

    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (state_number) REFERENCES car_accounting(state_number),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);

-- -----------------------------------------------------------
-- 3. Пакеты 
-- -----------------------------------------------------------

CREATE TABLE packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    arrival_id INT NOT NULL,
    blocks_count INT NOT NULL,
    defect_reason VARCHAR(255),

    FOREIGN KEY (arrival_id) REFERENCES arrivals(id)
);

-- -----------------------------------------------------------
-- 4. Фото и события 
-- -----------------------------------------------------------

CREATE TABLE event_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    arrival_id INT NOT NULL,
    event_time DATETIME NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100),
    camera_id INT,
    photo_path VARCHAR(255),

    FOREIGN KEY (arrival_id) REFERENCES arrivals(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);

INSERT INTO lgo_state_number (Tiem_Data, state_number) VALUES
('2025-02-10 08:12:34', 'A123BC116'),
('2025-02-10 09:05:11', 'M545MM777'),
('2025-02-10 09:33:50', 'K900XT152'),
('2025-02-10 10:41:02', 'H777OP198');
INSERT INTO cameras (ip_camera) VALUES
('192.168.1.10'),
('192.168.1.11'),
('192.168.1.12');
INSERT INTO car_accounting (state_number, Tiem_Data) VALUES
('A123BC116', '2025-02-10 08:12:34'),
('M545MM777', '2025-02-10 09:05:11'),
('K900XT152', '2025-02-10 09:33:50'),
('H777OP198', '2025-02-10 10:41:02');
INSERT INTO warehouses (name, type) VALUES
('Buffer', 'Transit'),
('Anode South', 'Anode'),
('Anode North', 'Anode'),
('Finished Products', 'Output');
INSERT INTO arrivals (warehouse_id, state_number, arrived_at, departed_at, camera_id, status) VALUES
(1, 'A123BC116', '2025-02-10 08:15:00', '2025-02-10 08:45:00', 1, 'completed'),
(2, 'M545MM777', '2025-02-10 09:10:00', NULL, 2, 'processing'),
(3, 'K900XT152', '2025-02-10 09:40:00', '2025-02-10 10:05:00', 3, 'completed'),
(4, 'H777OP198', '2025-02-10 10:45:00', NULL, 1, 'waiting');
INSERT INTO packages (arrival_id, blocks_count, defect_reason) VALUES
(1, 48, NULL),
(1, 50, 'damaged corner'),
(2, 52, NULL),
(3, 49, 'crack'),
(4, 50, NULL);
INSERT INTO event_log (arrival_id, event_type, camera_id, photo_path) VALUES
(1, 'arrived_photo', 1, '/photos/arrivals/1_in.jpg'),
(1, 'departed_photo', 1, '/photos/arrivals/1_out.jpg'),

(2, 'arrived_photo', 2, '/photos/arrivals/2_in.jpg'),

(3, 'arrived_photo', 3, '/photos/arrivals/3_in.jpg'),
(3, 'departed_photo', 3, '/photos/arrivals/3_out.jpg'),

(4, 'arrived_photo', 1, '/photos/arrivals/4_in.jpg');