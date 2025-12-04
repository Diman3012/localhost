-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Хост: 127.0.0.1:3306
-- Время создания: Дек 04 2025 г., 10:41
-- Версия сервера: 5.5.62
-- Версия PHP: 7.2.34

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `factory`
--

-- --------------------------------------------------------

--
-- Структура таблицы `admin_users`
--

CREATE TABLE `admin_users` (
  `id` int(11) NOT NULL,
  `login` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `admin_users`
--

INSERT INTO `admin_users` (`id`, `login`, `password`) VALUES
(1, 'admin', '12345');

-- --------------------------------------------------------

--
-- Структура таблицы `arrivals`
--

CREATE TABLE `arrivals` (
  `id` int(11) NOT NULL,
  `warehouse_id` int(11) NOT NULL,
  `state_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `arrived_at` datetime DEFAULT NULL,
  `departed_at` datetime DEFAULT NULL,
  `camera_id` int(11) DEFAULT NULL,
  `status_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `arrivals`
--

INSERT INTO `arrivals` (`id`, `warehouse_id`, `state_number`, `arrived_at`, `departed_at`, `camera_id`, `status_id`) VALUES
(1, 1, 'А123ВС', '2025-01-05 08:10:00', '2025-01-05 08:20:00', 1, 1),
(2, 1, 'О456РТ', '2025-01-05 09:00:00', '2025-01-05 09:40:00', 1, 2),
(3, 2, 'М789ЕХ', '2025-01-05 10:15:00', '2025-01-05 11:00:00', 3, 3),
(4, 3, 'А123ВС', '2025-01-05 11:30:00', '2025-01-05 12:10:00', 1, 2),
(5, 4, 'О456РТ', '2025-01-05 13:00:00', '2025-01-05 13:45:00', 3, 3),
(6, 4, 'М789ЕХ', '2025-01-05 14:00:00', '2025-01-05 14:50:00', 3, 3);

-- --------------------------------------------------------

--
-- Структура таблицы `block_statuses`
--

CREATE TABLE `block_statuses` (
  `id` int(11) NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `block_statuses`
--

INSERT INTO `block_statuses` (`id`, `name`) VALUES
(1, 'поврежден'),
(2, 'не поврежден');

-- --------------------------------------------------------

--
-- Структура таблицы `cameras`
--

CREATE TABLE `cameras` (
  `id` int(11) NOT NULL,
  `ip_camera` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `cameras`
--

INSERT INTO `cameras` (`id`, `ip_camera`, `type`) VALUES
(1, 'rtsp://192.168.0.101', 'учет'),
(2, 'rtsp://192.168.0.102', 'номера'),
(3, 'rtsp://192.168.0.103', 'учет'),
(4, 'rtsp://192.168.0.104', 'номера');

-- --------------------------------------------------------

--
-- Структура таблицы `event_log`
--

CREATE TABLE `event_log` (
  `id` int(11) NOT NULL,
  `arrival_id` int(11) NOT NULL,
  `event_time` datetime DEFAULT NULL,
  `event_type_id` int(11) NOT NULL,
  `camera_id` int(11) DEFAULT NULL,
  `photo_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `event_log`
--

INSERT INTO `event_log` (`id`, `arrival_id`, `event_time`, `event_type_id`, `camera_id`, `photo_path`) VALUES
(1, 2, NULL, 1, 2, '/photos/2_1.jpg'),
(2, 3, NULL, 2, 3, '/photos/3_1.jpg'),
(3, 5, NULL, 2, 4, '/photos/5_1.jpg');

-- --------------------------------------------------------

--
-- Структура таблицы `event_types`
--

CREATE TABLE `event_types` (
  `id` int(11) NOT NULL,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `event_types`
--

INSERT INTO `event_types` (`id`, `name`) VALUES
(1, 'фиксация номера'),
(2, 'фиксация разгрузки'),
(3, 'фиксация загрузки'),
(4, 'фиксация простоя');

-- --------------------------------------------------------

--
-- Структура таблицы `lgo_state_number`
--

CREATE TABLE `lgo_state_number` (
  `id` int(11) NOT NULL,
  `time_date` datetime NOT NULL,
  `state_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `lgo_state_number`
--

INSERT INTO `lgo_state_number` (`id`, `time_date`, `state_number`) VALUES
(1, '2025-12-04 10:07:26', 'А123ВС'),
(2, '2025-12-04 10:07:26', 'О456РТ'),
(3, '2025-12-04 10:07:26', 'М789ЕХ');

-- --------------------------------------------------------

--
-- Структура таблицы `packages`
--

CREATE TABLE `packages` (
  `id` int(11) NOT NULL,
  `arrival_id` int(11) NOT NULL,
  `blocks_count` int(11) NOT NULL,
  `block_status_id` int(11) NOT NULL,
  `comment` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `packages`
--

INSERT INTO `packages` (`id`, `arrival_id`, `blocks_count`, `block_status_id`, `comment`) VALUES
(1, 2, 5, 2, NULL),
(2, 2, 6, 2, NULL),
(3, 3, 5, 1, NULL),
(4, 4, 6, 2, NULL),
(5, 5, 4, 2, NULL),
(6, 6, 6, 1, NULL);

-- --------------------------------------------------------

--
-- Структура таблицы `statuses`
--

CREATE TABLE `statuses` (
  `id` int(11) NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `statuses`
--

INSERT INTO `statuses` (`id`, `name`) VALUES
(1, 'простой'),
(2, 'загрузка'),
(3, 'выгрузка');

-- --------------------------------------------------------

--
-- Структура таблицы `warehouses`
--

CREATE TABLE `warehouses` (
  `id` int(11) NOT NULL,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `account_camera` int(11) DEFAULT NULL,
  `camera_state_numbers` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `warehouses`
--

INSERT INTO `warehouses` (`id`, `name`, `type`, `account_camera`, `camera_state_numbers`) VALUES
(1, 'Буферный склад СПО', 'буферный', 1, 2),
(2, 'Южный склад анодов ОО', 'аноды', 3, 4),
(3, 'Северный склад анодов ОО', 'аноды', 1, 2),
(4, 'Склад готовой продукции', 'готовая продукция', 3, 4);

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `admin_users`
--
ALTER TABLE `admin_users`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `arrivals`
--
ALTER TABLE `arrivals`
  ADD PRIMARY KEY (`id`),
  ADD KEY `warehouse_id` (`warehouse_id`),
  ADD KEY `camera_id` (`camera_id`),
  ADD KEY `status_id` (`status_id`);

--
-- Индексы таблицы `block_statuses`
--
ALTER TABLE `block_statuses`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `cameras`
--
ALTER TABLE `cameras`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `event_log`
--
ALTER TABLE `event_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `arrival_id` (`arrival_id`),
  ADD KEY `event_type_id` (`event_type_id`),
  ADD KEY `camera_id` (`camera_id`);

--
-- Индексы таблицы `event_types`
--
ALTER TABLE `event_types`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `lgo_state_number`
--
ALTER TABLE `lgo_state_number`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `packages`
--
ALTER TABLE `packages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `arrival_id` (`arrival_id`),
  ADD KEY `block_status_id` (`block_status_id`);

--
-- Индексы таблицы `statuses`
--
ALTER TABLE `statuses`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `warehouses`
--
ALTER TABLE `warehouses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `account_camera` (`account_camera`),
  ADD KEY `camera_state_numbers` (`camera_state_numbers`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `admin_users`
--
ALTER TABLE `admin_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT для таблицы `arrivals`
--
ALTER TABLE `arrivals`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT для таблицы `block_statuses`
--
ALTER TABLE `block_statuses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT для таблицы `cameras`
--
ALTER TABLE `cameras`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT для таблицы `event_log`
--
ALTER TABLE `event_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT для таблицы `event_types`
--
ALTER TABLE `event_types`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT для таблицы `lgo_state_number`
--
ALTER TABLE `lgo_state_number`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT для таблицы `packages`
--
ALTER TABLE `packages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT для таблицы `statuses`
--
ALTER TABLE `statuses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT для таблицы `warehouses`
--
ALTER TABLE `warehouses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `arrivals`
--
ALTER TABLE `arrivals`
  ADD CONSTRAINT `arrivals_ibfk_1` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouses` (`id`),
  ADD CONSTRAINT `arrivals_ibfk_2` FOREIGN KEY (`camera_id`) REFERENCES `cameras` (`id`),
  ADD CONSTRAINT `arrivals_ibfk_3` FOREIGN KEY (`status_id`) REFERENCES `statuses` (`id`);

--
-- Ограничения внешнего ключа таблицы `event_log`
--
ALTER TABLE `event_log`
  ADD CONSTRAINT `event_log_ibfk_1` FOREIGN KEY (`arrival_id`) REFERENCES `arrivals` (`id`),
  ADD CONSTRAINT `event_log_ibfk_2` FOREIGN KEY (`event_type_id`) REFERENCES `event_types` (`id`),
  ADD CONSTRAINT `event_log_ibfk_3` FOREIGN KEY (`camera_id`) REFERENCES `cameras` (`id`);

--
-- Ограничения внешнего ключа таблицы `packages`
--
ALTER TABLE `packages`
  ADD CONSTRAINT `packages_ibfk_1` FOREIGN KEY (`arrival_id`) REFERENCES `arrivals` (`id`),
  ADD CONSTRAINT `packages_ibfk_2` FOREIGN KEY (`block_status_id`) REFERENCES `block_statuses` (`id`);

--
-- Ограничения внешнего ключа таблицы `warehouses`
--
ALTER TABLE `warehouses`
  ADD CONSTRAINT `warehouses_ibfk_1` FOREIGN KEY (`account_camera`) REFERENCES `cameras` (`id`),
  ADD CONSTRAINT `warehouses_ibfk_2` FOREIGN KEY (`camera_state_numbers`) REFERENCES `cameras` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
