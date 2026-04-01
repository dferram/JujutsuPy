import math


def calculate_euclidean_distance(p1, p2):
    """
    Calcula la Distancia Euclidiana L2 entre dos puntos (x, y).
    d(p1, p2) = sqrt((x2 - x1)^2 + (y2 - y1)^2)
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def get_centroid(hand_landmarks1, hand_landmarks2, frame_width, frame_height, offset_y=-180):
    """Halla el centroide proyectivo (punto medio espacial) entre ambas manos."""
    x1, y1 = hand_landmarks1.landmark[0].x, hand_landmarks1.landmark[0].y
    x2, y2 = hand_landmarks2.landmark[0].x, hand_landmarks2.landmark[0].y

    center_x = int(((x1 + x2) / 2) * frame_width)
    center_y = int(((y1 + y2) / 2) * frame_height)
    center_y += offset_y

    return center_x, center_y


def get_single_hand_center(hand_landmarks, frame_width, frame_height):
    """Retorna el centro de una sola mano en coordenadas de píxel."""
    cx = int(hand_landmarks.landmark[9].x * frame_width)   # Landmark 9 = centro de palma
    cy = int(hand_landmarks.landmark[9].y * frame_height)
    return cx, cy


def is_finger_extended(hand_landmarks, finger_tip_id, finger_pip_id):
    """
    Determina si un dedo está extendido comparando la coordenada Y
    de la punta (tip) vs. la articulación PIP. En coordenadas MediaPipe,
    Y más bajo = más arriba en pantalla, por tanto tip.y < pip.y = extendido.
    """
    tip = hand_landmarks.landmark[finger_tip_id]
    pip = hand_landmarks.landmark[finger_pip_id]
    return tip.y < pip.y


def is_thumb_extended(hand_landmarks):
    """
    El pulgar se extiende lateralmente, no verticalmente.
    Comparamos la distancia X del tip(4) vs IP(3) respecto a la muñeca(0).
    """
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    wrist = hand_landmarks.landmark[0]

    # Si el tip está más lejos de la muñeca que la articulación IP, está extendido
    dist_tip = abs(thumb_tip.x - wrist.x)
    dist_ip = abs(thumb_ip.x - wrist.x)
    return dist_tip > dist_ip


def get_extended_fingers(hand_landmarks):
    """
    Retorna una lista de 5 booleanos [thumb, index, middle, ring, pinky]
    indicando cuáles dedos están extendidos.
    """
    fingers = [
        is_thumb_extended(hand_landmarks),
        is_finger_extended(hand_landmarks, 8, 6),    # Índice
        is_finger_extended(hand_landmarks, 12, 10),   # Medio
        is_finger_extended(hand_landmarks, 16, 14),   # Anular
        is_finger_extended(hand_landmarks, 20, 18),   # Meñique
    ]
    return fingers


def landmarks_to_point(landmarks, idx):
    """Extrae (x, y) normalizado de un landmark por su índice."""
    return (landmarks.landmark[idx].x, landmarks.landmark[idx].y)
