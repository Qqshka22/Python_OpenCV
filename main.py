import cv2
import mediapipe as mp
import pyautogui
import time

# Инициализация MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.6,
                       min_tracking_confidence=0.6)
mp_drawing = mp.solutions.drawing_utils
# Настройка экрана и параметров
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
FRAME_REDUCTION = 100  # Размер рамки вокруг видео для уменьшения шума
SMOOTHING_FACTOR = 5  # Коэффициент сглаживания для более плавного движения
prev_x, prev_y = 0, 0
previous_palm_y = None  # Предыдущая координата Y центра ладони
SCROLL_THRESHOLD = 30  # Пороговое значение для скроллинга

# Функция для сглаживания движения курсора
def smooth_cursor_movement(screen_x, screen_y):
    global prev_x, prev_y
    current_x = prev_x + (screen_x - prev_x) / SMOOTHING_FACTOR
    current_y = prev_y + (screen_y - prev_y) / SMOOTHING_FACTOR
    prev_x, prev_y = current_x, current_y
    return int(current_x), int(current_y)

# Инициализация камеры
cap = cv2.VideoCapture(0)
cap.set(3, 600)
cap.set(4, 400)
# Получаем размер экрана
screen_width, screen_height = pyautogui.size()

# Флаги для отслеживания состояния нажатия ЛКМ
is_left_click_pressed = False
last_click_time = 0
double_click_interval = 0.3  # Интервал для двойного клика в секундах

# Переменные для отслеживания предыдущих координат большого пальца
prev_thumb_tip_y = None


def limit_fps(self, current_time, prev_time, fps):
    """Ограничивает частоту кадров до заданного значения."""
    interval = 1 / fps
    if current_time - prev_time >= interval:
        return True
    return False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    # Переводим изображение в RGB
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Получаем координаты ключевых точек
            landmarks = hand_landmarks.landmark

            # Координаты кончика указательного пальца (индекс 8)
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            # Координаты основания указательного пальца (индекс 5)
            index_mcp = landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP]

            # Координаты среднего сустава указательного пальца (индекс 6)
            index_pip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP]

            # Координаты кончика среднего пальца (индекс 12)
            middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            # Координаты основания среднего пальца (индекс 9)
            middle_mcp = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

            # Координаты среднего сустава среднего пальца (индекс 10)
            middle_pip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]

            # Координаты кончика большого пальца (индекс 4)
            thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

            # Координаты основания большого пальца (индекс 1)
            thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]

            # Координаты среднего сустава большого пальца (индекс 2)
            thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]

            # Координаты остальных пальцев
            ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
            ring_mcp = landmarks[mp_hands.HandLandmark.RING_FINGER_MCP]
            ring_pip = landmarks[mp_hands.HandLandmark.RING_FINGER_PIP]

            pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
            pinky_mcp = landmarks[mp_hands.HandLandmark.PINKY_MCP]
            pinky_pip = landmarks[mp_hands.HandLandmark.PINKY_PIP]

            # Вычисляем расстояния между ключевыми точками
            thumb_length = abs(thumb_tip.y - thumb_mcp.y)
            index_length = abs(index_tip.y - index_mcp.y)
            middle_length = abs(middle_tip.y - middle_mcp.y)
            ring_length = abs(ring_tip.y - ring_mcp.y)
            pinky_length = abs(pinky_tip.y - pinky_mcp.y)

            # Проверяем, вытянут ли указательный палец
            if (index_length > thumb_length and
                index_length > middle_length and
                index_length > ring_length and
                index_length > pinky_length):
                print("Указательный палец вытянут")

                # Преобразуем координаты кончика указательного пальца в координаты экрана
                index_x = int(index_tip.x * screen_width)
                index_y = int(index_tip.y * screen_height)

                # Перемещаем курсор
                pyautogui.moveTo(index_x, index_y)

                # Проверяем, сжаты ли указательный и средний пальцы
                distance_index_middle = ((index_tip.x - middle_tip.x) ** 2 + (index_tip.y - middle_tip.y) ** 2) ** 0.5
                print(f"Расстояние между указательным и средним пальцами: {distance_index_middle}")

                if distance_index_middle < 0.05:  # Пороговое значение для сжатия пальцев
                    if not is_left_click_pressed:
                        current_time = time.time()
                        if current_time - last_click_time < double_click_interval:
                            # Двойной клик
                            pyautogui.doubleClick(button='left')
                            print("Двойной клик")
                        else:
                            # Одиночный клик
                            pyautogui.mouseDown(button='left')
                            print("ЛКМ нажата")
                        is_left_click_pressed = True
                        last_click_time = current_time
                else:
                    if is_left_click_pressed:
                        pyautogui.mouseUp(button='left')
                        is_left_click_pressed = False
                        print("ЛКМ отпущена")

            # Проверяем, сжаты ли средний и большой пальцы
            distance_middle_thumb = ((middle_tip.x - thumb_tip.x) ** 2 + (middle_tip.y - thumb_tip.y) ** 2) ** 0.5
            print(f"Расстояние между средним и большим пальцами: {distance_middle_thumb}")

            if distance_middle_thumb < 0.05:  # Пороговое значение для сжатия пальцев
                if not is_left_click_pressed:
                    current_time = time.time()
                    if current_time - last_click_time < double_click_interval:
                        # Двойной клик
                        pyautogui.doubleClick(button='left')
                        print("Двойной клик")
                    else:
                        # Одиночный клик
                        pyautogui.mouseDown(button='left')
                        print("ЛКМ нажата")
                    is_left_click_pressed = True
                    last_click_time = current_time
            else:
                if is_left_click_pressed:
                    pyautogui.mouseUp(button='left')
                    is_left_click_pressed = False
                    print("ЛКМ отпущена")

            # Проверяем, закрыт ли кулак
            is_fist_closed = (thumb_length < 0.05 and
                              index_length < 0.05 and
                              middle_length < 0.05 and
                              ring_length < 0.05 and
                              pinky_length < 0.05)

            if is_fist_closed:
                print("Кулак закрыт")

                # Проверяем направление движения большого пальца
                if prev_thumb_tip_y is not None:
                    delta_y = thumb_tip.y - prev_thumb_tip_y

                    if delta_y > 0.01:  # Пороговое значение для движения вниз
                        pyautogui.scroll(-100)  # Скроллим вниз
                        print("Скролл вниз")
                    elif delta_y < -0.01:  # Пороговое значение для движения вверх
                        pyautogui.scroll(100)  # Скроллим вверх
                        print("Скролл вверх")

                prev_thumb_tip_y = thumb_tip.y
            else:
                prev_thumb_tip_y = None

            # Рисуем маркеры на руке
            # mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Закрашиваем кончик указательного пальца зеленым кругом
            index_tip_x = int(index_tip.x * frame.shape[1])
            index_tip_y = int(index_tip.y * frame.shape[0])
            cv2.circle(frame, (index_tip_x, index_tip_y), 10, (0, 255, 0), -1)

            # Закрашиваем кончик среднего пальца красным кругом
            middle_tip_x = int(middle_tip.x * frame.shape[1])
            middle_tip_y = int(middle_tip.y * frame.shape[0])
            cv2.circle(frame, (middle_tip_x, middle_tip_y), 10, (0, 0, 255), -1)

            # Закрашиваем кончик большого пальца синим кругом
            thumb_tip_x = int(thumb_tip.x * frame.shape[1])
            thumb_tip_y = int(thumb_tip.y * frame.shape[0])
            cv2.circle(frame, (thumb_tip_x, thumb_tip_y), 10, (255, 0, 0), -1)

    # Отображаем результат
    cv2.imshow('Hand Gesture Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()