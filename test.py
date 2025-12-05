from ultralytics import YOLO
import cv2
import numpy as np
import datetime
import os  # Добавлено для работы с путями

# 1. Загрузка обученной модели
# Используем сырую строку (raw string) или двойные обратные слеши
model_path = r'C:\OSPanel\domains\localhost\best.pt'  # Вариант 1: сырая строка
# model_path = 'C:\\OSPanel\\domains\\localhost\\best.pt'  # Вариант 2: двойные слеши
# model_path = 'C:/OSPanel/domains/localhost/best.pt'  # Вариант 3: прямой слеш (тоже работает)

# Проверка существования файла модели
if not os.path.exists(model_path):
    print(f"Ошибка: Файл модели не найден по пути: {model_path}")
    exit()

try:
    model = YOLO(model_path)
    print(f"Модель успешно загружена: {model_path}")
except Exception as e:
    print(f"Ошибка при загрузке модели: {e}")
    exit()

# 2. Настройка IP-камеры
ip_camera_url = 'rtsp://admin:PAROL123qwerty@10.21.110.173:554/live'
capture = cv2.VideoCapture(ip_camera_url)

if not capture.isOpened():
    print(f"Ошибка: Не удалось открыть IP-камеру по адресу {ip_camera_url}")
    exit()

# 3. Цвета для рисования рамок (зеленый) и имя класса
color = (0, 255, 0)
class_name = "грузовик_с_полуприцепом"

# 4. Переменные для отслеживания состояния
previous_truck_in_frame_state = False
stability_frames_threshold = 5 
current_stability_frames = 0

print("Начало мониторинга...")
print("Нажмите 'q' для выхода.")

# 5. Основной цикл обработки кадров
while True:
    ret, frame = capture.read()
    if not ret:
        print("Не удалось получить кадр с IP-камеры. Возможно, поток завершен.")
        break

    # Выполнение предсказания
    try:
        results = model(frame, conf=0.5, iou=0.7, verbose=False)[0]
    except Exception as e:
        print(f"Ошибка при выполнении детекции: {e}")
        break

    current_truck_in_frame_state = len(results.boxes) > 0

    # Обработка стабильности состояния (ИСПРАВЛЕНО)
    if current_truck_in_frame_state == previous_truck_in_frame_state:
        current_stability_frames += 1  # Увеличиваем счетчик, если состояние не изменилось
    else:
        current_stability_frames = 1  # Сбрасываем на 1, если состояние изменилось

    # Если состояние достаточно стабильно, обновляем его и логируем изменения
    if current_stability_frames >= stability_frames_threshold:
        # Проверяем, действительно ли состояние изменилось по сравнению с последним залогированным
        if current_truck_in_frame_state != previous_truck_in_frame_state:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if current_truck_in_frame_state:
                print(f"[{timestamp}] Грузовик ПОЯВИЛСЯ в кадре.")
            else:
                print(f"[{timestamp}] Грузовик ПРОПАЛ из кадра.")
            
            previous_truck_in_frame_state = current_truck_in_frame_state
            current_stability_frames = 0  # Сбрасываем счетчик после изменения состояния

    # Визуализация результатов
    if current_truck_in_frame_state:
        for box in results.boxes.xyxy.cpu().numpy().astype(np.int32):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Добавляем информационную панель
    status_text = "Грузовик в кадре" if current_truck_in_frame_state else "Грузовик не обнаружен"
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Стабильность: {current_stability_frames}/{stability_frames_threshold}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Отображение кадра
    cv2.imshow('Truck Detection', frame)

    # Выход по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
capture.release()
cv2.destroyAllWindows()
print("Мониторинг завершен.")
