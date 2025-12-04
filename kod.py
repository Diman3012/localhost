import pymysql
from pymysql import Error
from datetime import datetime

class AnodeBlockProcessor:
    def __init__(self):
        self.connection = None
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'factory',
            'port': 3306,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.connection = pymysql.connect(**self.config)
            print("✅ Подключение к базе данных установлено")
            return True
        except Error as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключение от базы данных"""
        if self.connection:
            self.connection.close()
            print("📴 Соединение с базой данных закрыто")
    
    def find_anode_warehouses(self):
        """Поиск складов с анодными блоками"""
        try:
            with self.connection.cursor() as cursor:
                # Ищем склады типа 'аноды'
                query = """
                    SELECT w.id, w.name, w.type, 
                           w.account_camera, w.camera_state_numbers
                    FROM warehouses w
                    WHERE w.type = 'аноды'
                """
                cursor.execute(query)
                warehouses = cursor.fetchall()
                
                print(f"\n📦 Найдено складов с анодными блоками: {len(warehouses)}")
                for wh in warehouses:
                    print(f"   Склад ID {wh['id']}: {wh['name']} ({wh['type']})")
                
                return warehouses
        except Error as e:
            print(f"❌ Ошибка при поиске складов: {e}")
            return []
    
    def get_anode_packages(self, warehouse_ids):
        """Получение пакетов анодных блоков с указанных складов"""
        if not warehouse_ids:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                # Формируем строку с ID складов
                ids_str = ','.join(str(id) for id in warehouse_ids)
                
                # Получаем все пакеты с анодных складов
                query = f"""
                    SELECT 
                        p.id as package_id,
                        p.arrival_id,
                        p.blocks_count,
                        bs.name as block_status,
                        p.comment,
                        a.warehouse_id,
                        a.state_number,
                        a.arrived_at,
                        a.departed_at,
                        w.name as warehouse_name,
                        w.type as warehouse_type
                    FROM packages p
                    JOIN arrivals a ON p.arrival_id = a.id
                    JOIN warehouses w ON a.warehouse_id = w.id
                    JOIN block_statuses bs ON p.block_status_id = bs.id
                    WHERE a.warehouse_id IN ({ids_str})
                    ORDER BY a.arrived_at DESC
                """
                
                cursor.execute(query)
                packages = cursor.fetchall()
                
                print(f"\n📊 Найдено пакетов с анодными блоками: {len(packages)}")
                return packages
        except Error as e:
            print(f"❌ Ошибка при получении пакетов: {e}")
            return []
    
    def analyze_anode_blocks(self, packages):
        """Анализ анодных блоков"""
        if not packages:
            print("\n⚠️ Анодные блоки не найдены")
            return
        
        total_blocks = 0
        damaged_blocks = 0
        good_blocks = 0
        warehouses_blocks = {}
        
        print("\n🔍 Анализ анодных блоков:")
        print("-" * 50)
        
        for pkg in packages:
            # Считаем общее количество блоков
            total_blocks += pkg['blocks_count']
            
            # Считаем поврежденные/неповрежденные блоки
            if pkg['block_status'] == 'поврежден':
                damaged_blocks += pkg['blocks_count']
            else:
                good_blocks += pkg['blocks_count']
            
            # Группируем по складам
            wh_id = pkg['warehouse_id']
            if wh_id not in warehouses_blocks:
                warehouses_blocks[wh_id] = {
                    'name': pkg['warehouse_name'],
                    'total': 0,
                    'damaged': 0
                }
            warehouses_blocks[wh_id]['total'] += pkg['blocks_count']
            if pkg['block_status'] == 'поврежден':
                warehouses_blocks[wh_id]['damaged'] += pkg['blocks_count']
            
            # Выводим информацию о пакете
            print(f"Пакет #{pkg['package_id']}:")
            print(f"  Склад: {pkg['warehouse_name']}")
            print(f"  Гос. номер: {pkg['state_number']}")
            print(f"  Количество блоков: {pkg['blocks_count']} шт.")
            print(f"  Статус: {pkg['block_status']}")
            print(f"  Прибыл: {pkg['arrived_at']}")
            if pkg['comment']:
                print(f"  Комментарий: {pkg['comment']}")
            print()
        
        # Выводим статистику
        print("=" * 50)
        print("📈 СТАТИСТИКА АНОДНЫХ БЛОКОВ:")
        print(f"Всего блоков: {total_blocks} шт.")
        print(f"Из них:")
        print(f"  ✓ Неповрежденных: {good_blocks} шт. ({good_blocks/total_blocks*100:.1f}%)")
        print(f"  ✗ Поврежденных: {damaged_blocks} шт. ({damaged_blocks/total_blocks*100:.1f}%)")
        
        print("\n📊 Распределение по складам:")
        for wh_id, data in warehouses_blocks.items():
            damaged_percent = data['damaged']/data['total']*100 if data['total'] > 0 else 0
            print(f"  {data['name']}: {data['total']} шт. (повреждено: {data['damaged']} шт., {damaged_percent:.1f}%)")
    
    def log_anode_processing(self, packages):
        """Запись результатов обработки в базу данных"""
        if not packages:
            return
        
        try:
            with self.connection.cursor() as cursor:
                # Проверяем, есть ли таблица для логирования
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS anode_processing_log (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        package_id INT NOT NULL,
                        warehouse_id INT NOT NULL,
                        state_number VARCHAR(100),
                        blocks_count INT,
                        block_status VARCHAR(100),
                        processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (package_id) REFERENCES packages(id),
                        FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Записываем каждый обработанный пакет
                for pkg in packages:
                    insert_query = """
                        INSERT INTO anode_processing_log 
                        (package_id, warehouse_id, state_number, blocks_count, block_status)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        processed_at = CURRENT_TIMESTAMP
                    """
                    
                    cursor.execute(insert_query, (
                        pkg['package_id'],
                        pkg['warehouse_id'],
                        pkg['state_number'],
                        pkg['blocks_count'],
                        pkg['block_status']
                    ))
                
                self.connection.commit()
                print(f"\n✅ Данные об анодных блоках записаны в базу данных")
                print(f"   Обработано пакетов: {len(packages)}")
                
        except Error as e:
            print(f"❌ Ошибка при записи в базу данных: {e}")
    
    def create_anode_summary(self):
        """Создание сводной таблицы по анодным блокам"""
        try:
            with self.connection.cursor() as cursor:
                # Создаем или обновляем представление
                cursor.execute("""
                    CREATE OR REPLACE VIEW anode_blocks_summary AS
                    SELECT 
                        w.id as warehouse_id,
                        w.name as warehouse_name,
                        COUNT(p.id) as total_packages,
                        SUM(p.blocks_count) as total_blocks,
                        SUM(CASE WHEN bs.name = 'поврежден' THEN p.blocks_count ELSE 0 END) as damaged_blocks,
                        SUM(CASE WHEN bs.name = 'не поврежден' THEN p.blocks_count ELSE 0 END) as good_blocks,
                        AVG(CASE WHEN bs.name = 'поврежден' THEN 1.0 ELSE 0.0 END) * 100 as damage_percentage
                    FROM packages p
                    JOIN arrivals a ON p.arrival_id = a.id
                    JOIN warehouses w ON a.warehouse_id = w.id
                    JOIN block_statuses bs ON p.block_status_id = bs.id
                    WHERE w.type = 'аноды'
                    GROUP BY w.id, w.name
                    ORDER BY total_blocks DESC
                """)
                
                # Получаем данные из представления
                cursor.execute("SELECT * FROM anode_blocks_summary")
                summary = cursor.fetchall()
                
                print("\n📋 СВОДКА ПО АНОДНЫМ БЛОКАМ:")
                print("=" * 70)
                print(f"{'Склад':<25} {'Пакеты':<10} {'Блоки':<10} {'Повреждено':<12} {'%':<8}")
                print("-" * 70)
                
                for row in summary:
                    print(f"{row['warehouse_name']:<25} "
                          f"{row['total_packages']:<10} "
                          f"{row['total_blocks']:<10} "
                          f"{row['damaged_blocks']:<12} "
                          f"{row['damage_percentage']:.1f}%")
                
                return summary
                
        except Error as e:
            print(f"❌ Ошибка при создании сводки: {e}")
            return []

def main():
    """Основная функция программы"""
    print("=" * 60)
    print("🔧 ПРОГРАММА УЧЕТА АНОДНЫХ БЛОКОВ")
    print("=" * 60)
    
    # Создаем процессор
    processor = AnodeBlockProcessor()
    
    # Подключаемся к базе данных
    if not processor.connect():
        print("Не удалось подключиться к базе данных. Программа завершена.")
        return
    
    try:
        # 1. Находим склады с анодными блоками
        anode_warehouses = processor.find_anode_warehouses()
        
        if not anode_warehouses:
            print("\n⚠️ Склады с анодными блоками не найдены в системе")
            processor.disconnect()
            return
        
        # Получаем ID складов
        warehouse_ids = [wh['id'] for wh in anode_warehouses]
        
        # 2. Получаем все пакеты с анодных складов
        packages = processor.get_anode_packages(warehouse_ids)
        
        # 3. Анализируем данные
        processor.analyze_anode_blocks(packages)
        
        # 4. Записываем результаты в базу данных
        processor.log_anode_processing(packages)
        
        # 5. Создаем сводную таблицу
        processor.create_anode_summary()
        
        print("\n" + "=" * 60)
        print("✅ Обработка анодных блоков завершена успешно!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n⚠️ Критическая ошибка: {e}")
    finally:
        # Закрываем соединение
        processor.disconnect()

if __name__ == "__main__":
    main()