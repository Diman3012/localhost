import pymysql
from pymysql import Error
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
import os
import threading
import time
import logging

class AnodeTruckMonitoringSystem:
    def __init__(self, camera_url, model_path, db_config):
        self.camera_url = camera_url
        self.model_path = model_path
        self.db_config = db_config
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Нейронная сеть
        self.model = None
        self.capture = None
        
        # Состояние системы
        self.truck_in_frame = False
        self.stability_frames = 0
        self.stability_threshold = 5
        self.last_truck_state = False
        
        # Данные о текущем грузовике
        self.current_truck = None
        
        # База данных
        self.connection = None
        self.cursor = None
        
        # Флаг работы
        self.running = False
    
    def initialize_neural_network(self):
        """Инициализация нейронной сети"""
        try:
            if not os.path.exists(self.model_path):
                self.logger.error(f"Файл модели не найден: {self.model_path}")
                return False
            
            self.model = YOLO(self.model_path)
            self.logger.info(f"Модель загружена: {self.model_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            return False
    
    def initialize_camera(self):
        """Инициализация камеры"""
        try:
            self.capture = cv2.VideoCapture(self.camera_url)
            if not self.capture.isOpened():
                self.logger.error(f"Не удалось открыть камеру: {self.camera_url}")
                return False
            self.logger.info(f"Камера подключена: {self.camera_url}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения камеры: {e}")
            return False
    
    def connect_to_database(self):
        """Подключение к базе данных"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            self.logger.info("Подключение к БД установлено")
            return True
        except Error as e:
            self.logger.error(f"Ошибка подключения к БД: {e}")
            return False
    
    def get_warehouse_info_by_camera(self):
        """Получение информации о складе по IP камеры"""
        try:
            # Извлекаем IP из URL камеры
            ip_part = self.camera_url.split('@')[1].split(':')[0] if '@' in self.camera_url else self.camera_url
            
            query = """
                SELECT w.id, w.name, w.type, c.id as camera_id
                FROM warehouses w
                JOIN cameras c ON w.account_camera = c.id
                WHERE c.ip_camera LIKE %s
            """
            
            self.cursor.execute(query, (f'%{ip_part}%',))
            result = self.cursor.fetchone()
            
            if result:
                self.logger.info(f"Найден склад: {result['name']} (ID: {result['id']})")
                return result
            
            self.logger.warning(f"Склад для камеры {ip_part} не найден")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при поиске склада: {e}")
            return None
    
    def create_arrival_record(self, warehouse_info, state_number):
        """Создание записи о прибытии"""
        try:
            now = datetime.now()
            
            query = """
                INSERT INTO arrivals 
                (warehouse_id, state_number, arrived_at, camera_id, status_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                warehouse_info['id'],
                state_number or 'НЕИЗВЕСТНО',
                now,
                warehouse_info['camera_id'],
                3  # статус "выгрузка"
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            arrival_id = self.cursor.lastrowid
            
            # Записываем событие в лог
            self.log_event(arrival_id, 2, warehouse_info['camera_id'])  # 2 = фиксация разгрузки
            
            self.logger.info(f"Запись о прибытии создана: ID {arrival_id}")
            
            # Сохраняем данные о текущем грузовике
            self.current_truck = {
                'arrival_id': arrival_id,
                'warehouse_id': warehouse_info['id'],
                'warehouse_name': warehouse_info['name'],
                'state_number': state_number or 'НЕИЗВЕСТНО',
                'arrived_at': now,
                'packages': [],
                'total_blocks': 0
            }
            
            return arrival_id
            
        except Error as e:
            self.logger.error(f"Ошибка при создании записи о прибытии: {e}")
            return None
    
    def update_arrival_departure(self):
        """Обновление записи о прибытии - установка времени отбытия"""
        if not self.current_truck:
            return False
        
        try:
            now = datetime.now()
            arrival_id = self.current_truck['arrival_id']
            
            query = "UPDATE arrivals SET departed_at = %s WHERE id = %s"
            self.cursor.execute(query, (now, arrival_id))
            self.connection.commit()
            
            # Записываем событие отбытия
            warehouse_info = self.get_warehouse_info_by_camera()
            if warehouse_info:
                self.log_event(arrival_id, 3, warehouse_info['camera_id'])  # 3 = фиксация загрузки
            
            # Выводим итоговую статистику
            self.print_arrival_summary()
            
            self.logger.info(f"Время отбытия установлено для arrival_id {arrival_id}")
            
            return True
        except Error as e:
            self.logger.error(f"Ошибка при обновлении записи: {e}")
            return False
    
    def log_event(self, arrival_id, event_type_id, camera_id):
        """Запись события в лог"""
        try:
            query = """
                INSERT INTO event_log 
                (arrival_id, event_time, event_type_id, camera_id)
                VALUES (%s, %s, %s, %s)
            """
            
            values = (
                arrival_id,
                datetime.now(),
                event_type_id,
                camera_id
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            event_type_name = {1: "фиксация номера", 2: "фиксация разгрузки", 
                              3: "фиксация загрузки", 4: "фиксация простоя"}.get(event_type_id, "неизвестно")
            
            self.logger.info(f"Событие записано: {event_type_name} для arrival_id {arrival_id}")
            
            return True
        except Error as e:
            self.logger.error(f"Ошибка записи события в лог: {e}")
            return False
    
    def add_package_record(self, blocks_count, block_status_id=2, comment=None):
        """Добавление записи о пакете"""
        if not self.current_truck:
            self.logger.warning("Попытка добавить пакет без активного грузовика")
            return None
        
        try:
            arrival_id = self.current_truck['arrival_id']
            
            # Получаем название статуса
            status_query = "SELECT name FROM block_statuses WHERE id = %s"
            self.cursor.execute(status_query, (block_status_id,))
            status_result = self.cursor.fetchone()
            status_name = status_result['name'] if status_result else 'неизвестно'
            
            query = """
                INSERT INTO packages 
                (arrival_id, blocks_count, block_status_id, comment)
                VALUES (%s, %s, %s, %s)
            """
            
            values = (
                arrival_id,
                blocks_count,
                block_status_id,
                comment or f"Добавлено автоматически в {datetime.now().strftime('%H:%M:%S')}"
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            package_id = self.cursor.lastrowid
            
            # Обновляем статистику текущего грузовика
            self.current_truck['packages'].append({
                'package_id': package_id,
                'blocks_count': blocks_count,
                'status_id': block_status_id,
                'status_name': status_name
            })
            
            self.current_truck['total_blocks'] += blocks_count
            
            self.logger.info(f"Добавлен пакет ID {package_id}: {blocks_count} блоков (статус: {status_name})")
            
            return package_id
        except Error as e:
            self.logger.error(f"Ошибка при добавлении пакета: {e}")
            return None
    
    def print_arrival_summary(self):
        """Вывод итоговой статистики по прибытию"""
        if not self.current_truck:
            return
        
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА ПО ГРУЗОВИКУ:")
        print(f"Склад: {self.current_truck['warehouse_name']}")
        print(f"Гос. номер: {self.current_truck['state_number']}")
        print(f"Время прибытия: {self.current_truck['arrived_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Всего пакетов: {len(self.current_truck['packages'])}")
        print(f"Всего анодных блоков: {self.current_truck['total_blocks']}")
        
        # Группировка по статусам
        status_counts = {}
        for pkg in self.current_truck['packages']:
            status_name = pkg['status_name']
            status_counts[status_name] = status_counts.get(status_name, 0) + pkg['blocks_count']
        
        print("Статусы блоков:")
        for status, count in status_counts.items():
            percentage = (count / self.current_truck['total_blocks']) * 100 if self.current_truck['total_blocks'] > 0 else 0
            print(f"  {status}: {count} шт. ({percentage:.1f}%)")
        
        print("=" * 60)
    
    def get_arrival_summary_from_db(self, arrival_id):
        """Получение сводки по arrival из базы данных"""
        try:
            query = """
                SELECT 
                    a.id,
                    a.state_number,
                    a.arrived_at,
                    a.departed_at,
                    w.name as warehouse_name,
                    COUNT(p.id) as package_count,
                    SUM(p.blocks_count) as total_blocks,
                    SUM(CASE WHEN bs.name = 'поврежден' THEN p.blocks_count ELSE 0 END) as damaged_blocks,
                    SUM(CASE WHEN bs.name = 'не поврежден' THEN p.blocks_count ELSE 0 END) as good_blocks
                FROM arrivals a
                JOIN warehouses w ON a.warehouse_id = w.id
                LEFT JOIN packages p ON a.id = p.arrival_id
                LEFT JOIN block_statuses bs ON p.block_status_id = bs.id
                WHERE a.id = %s
                GROUP BY a.id
            """
            
            self.cursor.execute(query, (arrival_id,))
            result = self.cursor.fetchone()
            
            return result
        except Error as e:
            self.logger.error(f"Ошибка при получении сводки: {e}")
            return None
    
    def detect_state_number(self, frame):
        """Обнаружение госномера (заглушка)"""
        # В реальной системе здесь должна быть нейронная сеть для распознавания номеров
        import random
        
        # Генерация тестового номера
        letters = ['А', 'В', 'Е', 'К', 'М', 'Н', 'О', 'Р', 'С', 'Т', 'У', 'Х']
        number = f"{random.choice(letters)}{random.randint(100, 999)}{random.choice(letters)}{random.choice(letters)}"
        
        # В реальной системе можно использовать OpenCV для поиска номерной пластины
        # и затем нейронную сеть для распознавания символов
        
        self.logger.info(f"Определен номер: {number}")
        return number
    
    def process_frame(self, frame):
        """Обработка одного кадра"""
        try:
            # Детекция грузовика
            results = self.model(frame, conf=0.5, iou=0.7, verbose=False)[0]
            current_truck_state = len(results.boxes) > 0
            
            # Проверка стабильности
            if current_truck_state == self.last_truck_state:
                self.stability_frames += 1
            else:
                self.stability_frames = 1
            
            # Если состояние стабилизировалось
            if self.stability_frames >= self.stability_threshold:
                # Грузовик появился
                if current_truck_state and not self.truck_in_frame:
                    print("\n🚚 Грузовик обнаружен - начинаем запись...")
                    self.truck_in_frame = True
                    
                    # Получаем информацию о складе
                    warehouse_info = self.get_warehouse_info_by_camera()
                    if not warehouse_info:
                        print("❌ Не удалось определить склад для камеры")
                        self.truck_in_frame = False
                        return frame
                    
                    # Определяем номер
                    state_number = self.detect_state_number(frame)
                    print(f"📋 Номер грузовика: {state_number}")
                    print(f"🏭 Склад: {warehouse_info['name']}")
                    
                    # Создаем запись в БД
                    if self.connection:
                        self.create_arrival_record(warehouse_info, state_number)
                
                # Грузовик уехал
                elif not current_truck_state and self.truck_in_frame:
                    print("\n🚚 Грузовик уехал - завершаем запись...")
                    self.truck_in_frame = False
                    
                    # Обновляем запись в БД
                    if self.connection and self.current_truck:
                        self.update_arrival_departure()
                        self.current_truck = None
                
                self.last_truck_state = current_truck_state
            
            # Визуализация
            if current_truck_state:
                for box in results.boxes.xyxy.cpu().numpy().astype(np.int32):
                    x1, y1, x2, y2 = box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "ГРУЗОВИК", (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Информационная панель
            status_color = (0, 255, 0) if self.truck_in_frame else (0, 0, 255)
            status_text = "📹 ЗАГРУЗКА" if self.truck_in_frame else "⏳ ОЖИДАНИЕ"
            cv2.putText(frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            if self.current_truck:
                cv2.putText(frame, f"Номер: {self.current_truck['state_number']}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Блоков: {self.current_truck['total_blocks']}", (10, 85), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.putText(frame, f"Стабильность: {self.stability_frames}/{self.stability_threshold}", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки кадра: {e}")
            return frame
    
    def simulate_package_processing(self):
        """Симуляция обработки пакетов"""
        import random
        
        while self.running:
            if self.current_truck:
                # Случайно решаем, добавлять ли пакет
                if random.random() < 0.15:  # 15% шанс каждый цикл
                    blocks_count = random.randint(1, 8)
                    status_id = random.choices([1, 2], weights=[0.2, 0.8])[0]  # 20% поврежденных
                    
                    self.add_package_record(
                        blocks_count,
                        status_id,
                        f"Автоматически: {blocks_count} блоков"
                    )
            
            time.sleep(1.5)  # Проверяем каждые 1.5 секунды
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        print("=" * 60)
        print("🚚 СИСТЕМА МОНИТОРИНГА ГРУЗОВИКОВ")
        print("📦 АВТОМАТИЧЕСКИЙ УЧЕТ АНОДНЫХ БЛОКОВ")
        print("=" * 60)
        
        # Инициализация компонентов
        if not self.initialize_neural_network():
            return
        
        if not self.initialize_camera():
            return
        
        if not self.connect_to_database():
            print("⚠️ Внимание: Работаем без базы данных")
            print("   Данные будут только выводиться на экран")
        
        self.running = True
        
        # Запускаем поток для симуляции обработки пакетов
        if self.connection:
            processing_thread = threading.Thread(target=self.simulate_package_processing)
            processing_thread.daemon = True
            processing_thread.start()
            print("✅ Симулятор обработки пакетов запущен")
        
        print("\n📹 Начало мониторинга...")
        print("   Нажмите 'q' для выхода")
        print("-" * 60)
        
        # Основной цикл обработки видео
        frame_count = 0
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print("❌ Ошибка чтения кадра с камеры")
                break
            
            frame_count += 1
            
            # Обрабатываем каждый кадр
            processed_frame = self.process_frame(frame)
            
            # Показываем информацию каждые 100 кадров
            if frame_count % 100 == 0:
                print(f"📊 Обработано кадров: {frame_count}")
                if self.current_truck:
                    print(f"   Текущий грузовик: {self.current_truck['state_number']}")
                    print(f"   Блоков загружено: {self.current_truck['total_blocks']}")
            
            # Отображение
            cv2.imshow('Система учета анодных блоков', processed_frame)
            
            # Выход по клавише 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n🛑 Завершение работы по команде пользователя")
                break
        
        # Завершение работы
        self.stop_monitoring()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        
        if self.capture:
            self.capture.release()
            print("✅ Камера отключена")
        
        cv2.destroyAllWindows()
        
        if self.connection:
            self.connection.close()
            print("✅ Соединение с БД закрыто")
        
        print("\n" + "=" * 60)
        print("✅ СИСТЕМА ЗАВЕРШИЛА РАБОТУ")
        print("=" * 60)


def main():
    """Основная функция"""
    # Конфигурация
    CAMERA_URL = 'rtsp://admin:PAROL123qwerty@10.21.110.173:554/live'
    MODEL_PATH = r'C:\OSPanel\domains\localhost\best.pt'
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'factory',
        'port': 3306,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # Создаем и запускаем систему
    monitoring_system = AnodeTruckMonitoringSystem(
        camera_url=CAMERA_URL,
        model_path=MODEL_PATH,
        db_config=DB_CONFIG
    )
    
    try:
        monitoring_system.start_monitoring()
    except KeyboardInterrupt:
        print("\n\n🛑 Программа прервана пользователем (Ctrl+C)")
        monitoring_system.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        monitoring_system.stop_monitoring()


if __name__ == "__main__":
    main()