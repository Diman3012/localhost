import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        print("Подключаюсь к базе...")

        connection = mysql.connector.connect(
            host="127.0.0.1",     # для OSPanel обязательно 127.0.0.1
            port=3306,            # если OSPanel использует другой порт — поменяй
            user="root",
            password="",          # в OSPanel по умолчанию ПУСТО
            database="factory",
            auth_plugin="mysql_native_password"
        )

        if connection.is_connected():
            print("✔ Успешное подключение к MySQL!")
            return connection

    except Error as e:
        print("❗ Ошибка MySQL:", e)
        return None


def example_query():
    conn = create_connection()
    if conn is None:
        print("❌ Соединение отсутствует, остановка.")
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cameras;")
        rows = cursor.fetchall()

        print("📸 Содержимое таблицы cameras:")
        for row in rows:
            print(row)

    except Error as e:
        print("❗ Ошибка при выполнении запроса:", e)

    finally:
        if conn.is_connected():
            conn.close()
            print("🔌 Соединение закрыто.")


# Запуск программы
example_query()
