import pymysql
from pymysql import Error

def check_mysql_connection():
    """Проверка подключения к MySQL с использованием PyMySQL"""
    connection = None
    
    # Параметры для OpenServer/OSPanel
    configs = [
        {
            'host': 'localhost',
            'user': 'root',
            'password': '',  # Обычно пустой пароль в OpenServer
            'database': 'factory',
            'port': 3306,
            'charset': 'utf8mb4'
        },
        {
            'host': '127.0.0.1',
            'user': 'root',
            'password': 'root',  # Иногда пароль "root"
            'database': 'factory',
            'port': 3306,
            'charset': 'utf8mb4'
        },
        # Без указания базы
        {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'port': 3306,
            'charset': 'utf8mb4'
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n🔍 Попытка {i}: {config}")
        try:
            connection = pymysql.connect(**config)
            
            print(f"✅ Успешное подключение!")
            
            with connection.cursor() as cursor:
                # Проверяем версию сервера
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"   Версия MySQL: {version}")
                
                # Проверяем текущую базу данных
                if 'database' in config:
                    cursor.execute("SELECT DATABASE()")
                    db_name = cursor.fetchone()[0]
                    print(f"   База данных: {db_name}")
            
            connection.close()
            return True
                
        except Error as e:
            print(f"❌ Ошибка: {e}")
    
    return False

# Проверяем подключение
if check_mysql_connection():
    print("\n🎉 MySQL работает корректно!")
else:
    print("\n⚠️ Не удалось подключиться к MySQL")