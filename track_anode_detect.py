from ultralytics import YOLO
import cv2
import numpy as np
import datetime
from shapely.geometry import Point, Polygon 

# Для поддержки кириллицы в OpenCV
from PIL import Image, ImageDraw, ImageFont

# ===================================================================================
# --- КОНФИГУРАЦИЯ ---
# ===================================================================================

# --- Пути к вашим обученным моделям YOLOv8 ---
MODEL_TRUCK_PATH = 'C:/Users/RomashovVV/Desktop/движение анодов/py/runs/detect/train_truck/weights/best.pt'
MODEL_ANODES_PATH = 'C:/Users/RomashovVV/Desktop/движение анодов/py/runs/detect/train_anodes/weights/best.pt'

# --- URL IP-камеры ---
IP_CAMERA_URL = 'rtsp://admin:PAROL123qwerty@10.21.110.173:554/live'

# --- Пороги уверенности для детекции и IoU для NMS ---
CONF_THRESHOLD_TRUCK = 0.5
CONF_THRESHOLD_ANODES = 0.5
IOU_THRESHOLD = 0.7

# --- Цвета для отрисовки рамок и полигонов (в формате BGR для OpenCV) ---
COLOR_TRUCK = (0, 255, 0)   # Зеленый (BGR)
COLOR_ANODES = (255, 0, 0)  # Зеленый (BGR)
COLOR_ROI = (0, 255, 255)   # Желтый (BGR)

# --- Имена классов ---
CLASS_NAME_TRUCK = "Грузовик"
CLASS_NAME_ANODES = "Аноды"

# --- Параметр для сглаживания ложных срабатываний ---
STABILITY_FRAMES_THRESHOLD = 5 

# --- Определение области интереса (ROI) ---
# !!! ВАЖНО: СКОРРЕКТИРУЙТЕ ЭТИ ТОЧКИ ПОД ВАШЕ ИЗОБРАЖЕНИЕ !!!
roi_polygon_coords = np.array([[560, 220], [715, 190], [1717, 873], [1555, 1077], [1386, 1080], [584, 360]], np.int32)

# --- Настройки шрифта для кириллицы ---
# !!! ОБЯЗАТЕЛЬНО УКАЖИТЕ ПРАВИЛЬНЫЙ ПУТЬ К .TTF ФАЙЛУ ШРИФТА НА ВАШЕЙ СИСТЕМЕ !!!
# Пример для Windows:
FONT_PATH = "C:/Windows/Fonts/arial.ttf" 
# Пример для Linux/macOS:
# FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" 

FONT_SIZE = 20 # Размер шрифта

# ===================================================================================
# --- ИНИЦИАЛИЗАЦИЯ ---
# ===================================================================================

# --- Создаем объект Polygon для библиотеки shapely ---
roi_shapely_polygon = Polygon(roi_polygon_coords.reshape(-1, 2))

# --- Загрузка обученных моделей YOLOv8 ---
try:
    model_truck = YOLO(MODEL_TRUCK_PATH)
    model_anodes = YOLO(MODEL_ANODES_PATH)
    print("Модели YOLOv8 успешно загружены.")
except Exception as e:
    print(f"Ошибка загрузки моделей: {e}")
    print("Пожалуйста, убедитесь, что пути к файлам best.pt корректны.")
    exit()

# --- Инициализация видеопотока с IP-камеры ---
capture = cv2.VideoCapture(IP_CAMERA_URL)
if not capture.isOpened():
    print(f"Ошибка: Не удалось открыть IP-камеру по адресу {IP_CAMERA_URL}")
    exit()
print(f"Успешное подключение к IP-камере: {IP_CAMERA_URL}")

# --- Инициализация шрифта Pillow ---
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    print(f"Шрифт '{FONT_PATH}' загружен успешно.")
except IOError:
    print(f"Ошибка: Не удалось загрузить шрифт по пути '{FONT_PATH}'.")
    print("Убедитесь, что путь к .ttf файлу корректен и файл существует.")
    exit()

# --- Переменные для отслеживания состояния грузовика и анодов ---
truck_in_roi_state = False              
initial_anode_count = 0                 
final_anode_count = 0                   
first_detection_in_roi_processed = False 

# Переменные для механизма сглаживания
current_stability_frames_truck_in_roi = 0
previous_truck_in_roi_detection = False 

print("Начало мониторинга движения грузовиков и анодов...")

# ===================================================================================
# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
# ===================================================================================

def get_current_timestamp():
    """Возвращает текущее время в отформатированной строке."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_box_center_in_roi(box_coords, roi_polygon_obj):
    """Проверяет, находится ли центр ограничивающей рамки внутри полигона ROI."""
    x1, y1, x2, y2 = box_coords
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    point = Point(center_x, center_y)
    return roi_polygon_obj.contains(point)

def is_anode_on_truck(anode_box_coords, truck_box_coords):
    """
    Проверяет, находится ли центр анода внутри рамки грузовика.
    """
    if truck_box_coords is None:
        return False

    center_anode_x = (anode_box_coords[0] + anode_box_coords[2]) / 2
    center_anode_y = (anode_box_coords[1] + anode_box_coords[3]) / 2
    
    return (truck_box_coords[0] <= center_anode_x <= truck_box_coords[2]) and \
           (truck_box_coords[1] <= center_anode_y <= truck_box_coords[3])

def draw_text_pil(img_np, text, org, font_pil, color_bgr=(0, 255, 0), thickness=2):
    """
    Отрисовывает текст на изображении NumPy, используя Pillow для поддержки кириллицы.
    img_np: numpy array (изображение OpenCV в формате BGR)
    text: строка для отрисовки
    org: (x, y) - координаты верхнего левого угла текста
    font_pil: объект ImageFont из Pillow
    color_bgr: цвет текста в формате BGR
    thickness: толщина текста (игнорируется Pillow, т.к. текст уже отрисован)
    """
    # Преобразуем изображение из BGR в RGB для Pillow
    img_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    # Цвет для Pillow в формате RGB
    color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])

    # Отрисовываем текст
    draw.text(org, text, font=font_pil, fill=color_rgb)

    # Преобразуем изображение обратно в формат OpenCV (BGR)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ===================================================================================
# --- ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ КАДРОВ ---
# ===================================================================================

while True:
    ret, frame = capture.read()
    if not ret:
        print(f"[{get_current_timestamp()}] Не удалось получить кадр с IP-камеры. Поток, возможно, завершен.")
        break

    # 1. Детекция грузовика
    results_truck = model_truck(frame, conf=CONF_THRESHOLD_TRUCK, iou=IOU_THRESHOLD, verbose=False)[0]
    
    current_truck_detected = False 
    current_truck_in_roi_detection = False 
    truck_bbox_coords = None 

    if len(results_truck.boxes) > 0:
        current_truck_detected = True
        truck_bbox_coords = results_truck.boxes.xyxy[0].cpu().numpy().astype(np.int32)
        
        if is_box_center_in_roi(truck_bbox_coords, roi_shapely_polygon):
            current_truck_in_roi_detection = True

    # --- Механизм сглаживания и логирование событий ---
    
    if current_truck_in_roi_detection == previous_truck_in_roi_detection:
        current_stability_frames_truck_in_roi = 0 
    else:
        current_stability_frames_truck_in_roi += 1

    if current_stability_frames_truck_in_roi >= STABILITY_FRAMES_THRESHOLD:
        
        # --- Событие: Грузовик СТАБИЛЬНО въехал в ROI ---
        if current_truck_in_roi_detection and not truck_in_roi_state:
            print(f"[{get_current_timestamp()}] Грузовик ВЪЕХАЛ в область интереса.")
            truck_in_roi_state = True
            first_detection_in_roi_processed = True 
            initial_anode_count = 0 

        # --- Событие: Грузовик СТАБИЛЬНО выехал из ROI ---
        elif not current_truck_in_roi_detection and truck_in_roi_state:
            print(f"[{get_current_timestamp()}] Грузовик ВЫЕХАЛ из области интереса.")
            truck_in_roi_state = False
            
            results_anodes_final = model_anodes(frame, conf=CONF_THRESHOLD_ANODES, iou=IOU_THRESHOLD, verbose=False)[0]
            final_anode_count = 0
            
            if truck_bbox_coords is not None: 
                for anode_box_coords in results_anodes_final.boxes.xyxy.cpu().numpy().astype(np.int32):
                    if is_anode_on_truck(anode_box_coords, truck_bbox_coords):
                        final_anode_count += 1
            else: 
                for anode_box_coords in results_anodes_final.boxes.xyxy.cpu().numpy().astype(np.int32):
                    if is_box_center_in_roi(anode_box_coords, roi_shapely_polygon):
                         final_anode_count += 1

            if initial_anode_count == 0: 
                print(f"[{get_current_timestamp()}] Грузовик уехал с {final_anode_count} пакетами анодов.")
            else: 
                unloaded_count = initial_anode_count - final_anode_count
                if unloaded_count > 0:
                    print(f"[{get_current_timestamp()}] Грузовик выгрузил {unloaded_count} пакетов анодов. Осталось {final_anode_count}.")
                elif unloaded_count < 0: 
                    print(f"[{get_current_timestamp()}] Грузовик уехал с {final_anode_count} пакетами анодов (загружено {abs(unloaded_count)}).")
                else: 
                    print(f"[{get_current_timestamp()}] Грузовик уехал с {final_anode_count} пакетами анодов (количество не изменилось).")
            
            initial_anode_count = 0 
        
        previous_truck_in_roi_detection = current_truck_in_roi_detection
        current_stability_frames_truck_in_roi = 0

    # --- Логика: Первый кадр с грузовиком в ROI (однократная проверка анодов) ---
    if first_detection_in_roi_processed and truck_bbox_coords is not None:
        first_detection_in_roi_processed = False 
        
        results_anodes_initial = model_anodes(frame, conf=CONF_THRESHOLD_ANODES, iou=IOU_THRESHOLD, verbose=False)[0]
        initial_anode_count = 0
        
        for anode_box_coords in results_anodes_initial.boxes.xyxy.cpu().numpy().astype(np.int32):
            if is_anode_on_truck(anode_box_coords, truck_bbox_coords):
                initial_anode_count += 1

        if initial_anode_count == 0:
            print(f"[{get_current_timestamp()}] Прибыл ПУСТОЙ грузовик.")
        else:
            print(f"[{get_current_timestamp()}] Прибыл грузовик С АНОДАМИ ({initial_anode_count} пакетов).")
            
    # ===================================================================================
    # --- ВИЗУАЛИЗАЦИЯ НА КАДРЕ ---
    # ===================================================================================
    
    # 1. Отрисовка полигона ROI
    cv2.polylines(frame, [roi_polygon_coords], isClosed=True, color=COLOR_ROI, thickness=1)

    # 2. Отрисовка рамки грузовика, если обнаружен
    if truck_bbox_coords is not None:
        x1, y1, x2, y2 = truck_bbox_coords
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_TRUCK, 2)
        # Использование Pillow для отрисовки текста
        frame = draw_text_pil(frame, CLASS_NAME_TRUCK, (x1, y1 - FONT_SIZE - 5), font, COLOR_TRUCK)

        # 3. Отрисовка рамок анодов, если грузовик в ROI и аноды обнаружены
        if truck_in_roi_state: 
             results_anodes_viz = model_anodes(frame, conf=CONF_THRESHOLD_ANODES, iou=IOU_THRESHOLD, verbose=False)[0]
             for anode_box_coords in results_anodes_viz.boxes.xyxy.cpu().numpy().astype(np.int32):
                if is_anode_on_truck(anode_box_coords, truck_bbox_coords):
                    x1_a, y1_a, x2_a, y2_a = anode_box_coords
                    cv2.rectangle(frame, (x1_a, y1_a), (x2_a, y2_a), COLOR_ANODES, 2)
                    # Использование Pillow для отрисовки текста
                    frame = draw_text_pil(frame, CLASS_NAME_ANODES, (x1_a, y1_a - FONT_SIZE - 5), font, COLOR_ANODES)
                
    # Отображение обработанного кадра
    cv2.imshow('Truck and Anode Monitoring', frame)

    # Условие выхода из цикла по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ===================================================================================
# --- ЗАВЕРШЕНИЕ РАБОТЫ ---
# ===================================================================================

capture.release()
cv2.destroyAllWindows()
print("Мониторинг завершен.")