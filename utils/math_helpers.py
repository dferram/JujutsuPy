import math

def calculate_euclidean_distance(p1, p2):
    """Calcula la distancia Euclidiana L2 entre dos puntos (x, y)."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def get_centroid(hand_landmarks1, hand_landmarks2, frame_width, frame_height, offset_y=-180):
    """Halla el centroide proyectivo (punto medio espacial) entre ambas manos."""
    x1, y1 = hand_landmarks1.landmark[0].x, hand_landmarks1.landmark[0].y
    x2, y2 = hand_landmarks2.landmark[0].x, hand_landmarks2.landmark[0].y
    
    # Mapeo de espacio L2 ([0,1]) a espacio Píxel
    center_x = int(((x1 + x2) / 2) * frame_width)
    center_y = int(((y1 + y2) / 2) * frame_height)
    
    # Offset: el Shikigami emerge "sobre" las manos
    center_y += offset_y
    
    return center_x, center_y
