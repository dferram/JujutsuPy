"""
core/gestures.py — Módulo central de Detección de Gestos (Sellos de Mano)

Cada función valida una firma geométrica específica basada en las posiciones
relativas de los Landmarks de MediaPipe. Retorna True si el gesto coincide.

Landmarks clave de MediaPipe:
  0  = Muñeca
  4  = Punta del pulgar
  8  = Punta del índice
  12 = Punta del medio
  16 = Punta del anular
  20 = Punta del meñique
  9  = Centro de la palma (base del dedo medio)
  5  = Base del índice (MCP)
"""

from utils.math_helpers import (
    calculate_euclidean_distance,
    landmarks_to_point,
    get_extended_fingers,
    is_finger_extended,
    is_thumb_extended,
)
import time


# =============================================================================
#  MEGUMI FUSHIGURO — Ten Shadows Technique (7 técnicas)
# =============================================================================

def detect_divine_dogs(h1, h2):
    """
    Divine Dog (Ken): Palmas unidas lateralmente con dedos entrelazados, pulgares hacia arriba (Orejas).
    Firma: Base de las palmas muy cercanas + Puntas de pulgares por encima (Y menor) de sus respectivas MCPs.
    """
    w1, w2 = landmarks_to_point(h1, 0), landmarks_to_point(h2, 0)
    p1, p2 = landmarks_to_point(h1, 9), landmarks_to_point(h2, 9)

    # Palmas/Muñecas pegadas (Sombra de perro lateral)
    dist_wrists = calculate_euclidean_distance(w1, w2)
    dist_palms = calculate_euclidean_distance(p1, p2)

    if dist_wrists > 0.15 or dist_palms > 0.15:
        return False

    # Pulgares hacia arriba (MediaPipe Y axis goes down, so tip Y < mcp Y)
    thumb1_up = h1.landmark[4].y < h1.landmark[2].y
    thumb2_up = h2.landmark[4].y < h2.landmark[2].y

    return thumb1_up and thumb2_up


def detect_nue(h1, h2):
    """
    Nue (Búho): Muñecas cruzadas, manos abiertas con dedos extendidos (alas).
    Firma: Muñecas cruzadas en Y + todos los dedos extendidos en ambas manos.
    """
    w1, w2 = landmarks_to_point(h1, 0), landmarks_to_point(h2, 0)
    dist_wrists = calculate_euclidean_distance(w1, w2)

    # Muñecas deben estar cercanas (cruzadas)
    if dist_wrists > 0.25:
        return False

    # Todos los dedos (menos pulgar) deben estar extendidos en ambas manos
    fingers1 = get_extended_fingers(h1)
    fingers2 = get_extended_fingers(h2)

    # Al menos 4 dedos extendidos por mano (índice, medio, anular, meñique)
    return sum(fingers1[1:]) >= 4 and sum(fingers2[1:]) >= 4


# Se eliminó la técnica Great Serpent (Orochi) a petición del usuario.

def detect_toad(h1, h2):
    """
    Toad (Gama): Dedos entrelazados, índices y medios proyectados.
    Firma: Palmas muy cercanas + índices y medios extendidos + anulares y meñiques no.
    """
    p1, p2 = landmarks_to_point(h1, 9), landmarks_to_point(h2, 9)
    if calculate_euclidean_distance(p1, p2) > 0.12:
        return False

    f1 = get_extended_fingers(h1)
    f2 = get_extended_fingers(h2)

    # Índice y medio extendidos, anular y meñique cerrados
    cond1 = f1[1] and f1[2] and not f1[3] and not f1[4]
    cond2 = f2[1] and f2[2] and not f2[3] and not f2[4]

    return cond1 and cond2


def detect_max_elephant(h1, h2):
    """
    Max Elephant: Manos espalda con espalda, pulgares apuntando abajo.
    Firma: Muñecas muy cercanas (< 0.15) + pulgares apuntando abajo (tip.y > wrist.y).
    """
    w1, w2 = landmarks_to_point(h1, 0), landmarks_to_point(h2, 0)
    if calculate_euclidean_distance(w1, w2) > 0.15:
        return False

    # Pulgares deben apuntar hacia abajo (tip Y > wrist Y en MediaPipe)
    thumb1_down = h1.landmark[4].y > h1.landmark[0].y
    thumb2_down = h2.landmark[4].y > h2.landmark[0].y

    return thumb1_down and thumb2_down


def detect_rabbit_escape(h1, h2):
    """
    Rabbit Escape: "V" (paz) pegadas a los lados de la cabeza.
    Firma: Ambas manos en V + posición alta en la cámara (y < 0.35).
    """
    f1 = get_extended_fingers(h1)
    f2 = get_extended_fingers(h2)

    # Ambas manos en V: índice y medio arriba, el resto abajo
    v1 = f1[1] and f1[2] and not f1[3] and not f1[4]
    v2 = f2[1] and f2[2] and not f2[3] and not f2[4]

    if not (v1 and v2):
        return False

    # Las manos deben estar elevadas (cerca de la cabeza)
    y1 = h1.landmark[0].y
    y2 = h2.landmark[0].y

    return y1 < 0.40 and y2 < 0.40


def detect_mahoraga(h1, h2):
    """
    Mahoraga (Eight-Handled Sword): Ambos puños cerrados, uno encima del otro.
    Firma: Ambas manos son puños (dedos recogidos) + Muñecas muy cercanas vertical/espacialmente (< 0.25).
    """
    w1, w2 = landmarks_to_point(h1, 0), landmarks_to_point(h2, 0)
    
    # Validar puños cerrados (puntas cerca de la muñeca)
    tips1 = [landmarks_to_point(h1, i) for i in [8, 12, 16, 20]]
    tips2 = [landmarks_to_point(h2, i) for i in [8, 12, 16, 20]]
    
    is_fist_1 = all(calculate_euclidean_distance(t, w1) < 0.15 for t in tips1)
    is_fist_2 = all(calculate_euclidean_distance(t, w2) < 0.15 for t in tips2)
    
    if not (is_fist_1 and is_fist_2):
        return False
        
    # Validar que están cerca uno del otro (apilados)
    dist_wrists = calculate_euclidean_distance(w1, w2)
    return dist_wrists < 0.25


# =============================================================================
#  KENTO NANAMI — Ratio Technique (2 técnicas)
# =============================================================================

class NanamiState:
    """Maneja el estado temporal de Nanami (Overtime requiere mantener el puño)."""
    def __init__(self):
        self.fist_start_time = None
        self.overtime_active = False
        self.OVERTIME_HOLD_SECONDS = 2.0

    def reset(self):
        self.fist_start_time = None
        self.overtime_active = False


_nanami_state = NanamiState()


def detect_overtime(hand):
    """
    Overtime Mode: Puño cerrado sostenido por 2 segundos.
    Firma: Todos los tips (8,12,16,20) cerca de la palma (0) < 0.1.
    """
    global _nanami_state
    wrist = landmarks_to_point(hand, 0)
    tips = [landmarks_to_point(hand, i) for i in [8, 12, 16, 20]]

    is_fist = all(calculate_euclidean_distance(t, wrist) < 0.15 for t in tips)

    if is_fist:
        if _nanami_state.fist_start_time is None:
            _nanami_state.fist_start_time = time.time()
        elif time.time() - _nanami_state.fist_start_time >= _nanami_state.OVERTIME_HOLD_SECONDS:
            _nanami_state.overtime_active = True
            return True
    else:
        _nanami_state.fist_start_time = None
        _nanami_state.overtime_active = False

    return False


def detect_ratio(hand):
    """
    Ratio 7:3: Mano de cuchillo (palma abierta de lado, dedos juntos, pulgar recogido).
    Firma: 4 dedos extendidos, todos muy juntos entre sí, pulgar recogido.
    """
    fingers = get_extended_fingers(hand)

    # 4 dedos extendidos y pulgar recogido
    if not (fingers[1] and fingers[2] and fingers[3] and fingers[4] and not fingers[0]):
        return False

    # Verificar que los dedos están juntos (no spread)
    tips = [landmarks_to_point(hand, i) for i in [8, 12, 16, 20]]
    max_dist = 0
    for i in range(len(tips)):
        for j in range(i + 1, len(tips)):
            d = calculate_euclidean_distance(tips[i], tips[j])
            if d > max_dist:
                max_dist = d

    return max_dist < 0.12


# REMOVED HIGURUMA


# =============================================================================
#  SATORU GOJO — Limitless / Six Eyes (4 técnicas)
# =============================================================================

def detect_infinite_void(hand):
    """
    Infinite Void (Domain Expansion): Dedo corazón cruzado sobre el índice.
    Firma: Middle tip (12) cruza por encima del index tip (8) en eje X,
    ambos extendidos, y los demás dedos cerrados.
    """
    fingers = get_extended_fingers(hand)

    # Índice y medio extendidos, anular y meñique cerrados
    if not (fingers[1] and fingers[2] and not fingers[3] and not fingers[4]):
        return False

    # El medio cruza sobre el índice (sus puntas X deben estar invertidas
    # respecto a sus bases)
    idx_tip = hand.landmark[8]
    mid_tip = hand.landmark[12]
    idx_mcp = hand.landmark[5]
    mid_mcp = hand.landmark[9]

    # En la mano derecha natural: mid.x > idx.x en la base.
    # Si están cruzados: mid_tip.x < idx_tip.x (o viceversa según lateralidad)
    base_diff = mid_mcp.x - idx_mcp.x
    tip_diff = mid_tip.x - idx_tip.x

    # Si el signo cambia, los dedos están cruzados
    return (base_diff * tip_diff) < 0


def detect_blue(hand):
    """
    Blue (Lapse): Mano abierta hacia la cámara (todos los dedos extendidos y separados).
    Firma: 5 dedos extendidos + spread (distancia entre índice y meñique > 0.15).
    """
    fingers = get_extended_fingers(hand)
    if sum(fingers) < 5:
        return False

    # Los dedos deben estar abiertos (spread)
    idx = landmarks_to_point(hand, 8)
    pinky = landmarks_to_point(hand, 20)
    spread = calculate_euclidean_distance(idx, pinky)

    return spread > 0.15


def detect_red(hand):
    """
    Red (Reversal): Solo el índice apuntando estrictamente hacia arriba.
    Firma: Índice extendido, pulgar recogido, todos los demás cerrados. Posición vertical estricta.
    """
    fingers = get_extended_fingers(hand)
    idx_up = fingers[1] and not fingers[0] and not fingers[2] and not fingers[3] and not fingers[4]

    # Validar que apunte hacia ARRIBA de forma global
    # Tip del índice más arriba que su base, y la base más arriba que la muñeca
    is_vertical = (hand.landmark[8].y < hand.landmark[5].y) and (hand.landmark[5].y < hand.landmark[0].y)

    return idx_up and is_vertical


def detect_hollow_purple(hand):
    """
    Hollow Purple (Shooting Pose con una mano).
    Firma: Poses de 'Pistola' (Shooting Pose) -> Índice y pulgar extendidos (o índice y medio), demás cerrados.
    El usuario especificó 1 sola mano.
    """
    fingers = get_extended_fingers(hand)

    # Pose de pistola clásica (pulgar e índice)
    gun_pose_1 = fingers[0] and fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]
    
    # Pose de "bang" anime (índice y medio, pulgar puede estar extendido o no)
    gun_pose_2 = fingers[1] and fingers[2] and not fingers[3] and not fingers[4]

    return gun_pose_1 or gun_pose_2


# REMOVED YUTA


# =============================================================================
#  DISPATCHER PRINCIPAL — Máquina de Detección Multi-Técnica
# =============================================================================

# Mapeo: ID → (nombre_display, character)
TECHNIQUE_INFO = {
    # Gojo
    "infinite_void":  ("DOMAIN: INFINITE VOID", "Gojo"),
    "blue":           ("CURSED TECHNIQUE LAPSE: BLUE", "Gojo"),
    "red":            ("CURSED TECHNIQUE REVERSAL: RED", "Gojo"),
    "hollow_purple":  ("HOLLOW PURPLE: IMAGINARY TECHNIQUE", "Gojo"),
    # Megumi
    "divine_dogs":    ("DIVINE DOGS: KEN", "Megumi"),
    "nue":            ("NUE: THUNDERBIRD", "Megumi"),
    "max_elephant":   ("MAX ELEPHANT", "Megumi"),
    "rabbit_escape":  ("RABBIT ESCAPE", "Megumi"),
    "mahoraga":       ("MAHORAGA: EIGHT-HANDLED SWORD", "Megumi"),
    # Nanami
    "overtime":       ("OVERTIME MODE", "Nanami"),
    "ratio":          ("RATIO TECHNIQUE: 7:3", "Nanami"),
}


def detect_active_technique(hands_list, handedness_list=None):
    """
    Dispatcher principal. Evalúa secuencialmente todas las firmas geométricas.
    
    Args:
        hands_list: Lista de hand_landmarks detectados por MediaPipe.
        handedness_list: Lista de clasificaciones de mano (izquierda/derecha).
    
    Returns:
        tuple: (technique_id: str, hand_data: dict) o (None, None).
               hand_data contiene las landmarks relevantes para centroide/efecto.
    """
    num_hands = len(hands_list) if hands_list else 0

    if num_hands == 2:
        h1, h2 = hands_list[0], hands_list[1]

        # --- Técnicas de 2 manos (orden de prioridad) ---
        if detect_mahoraga(h1, h2):
            return "mahoraga", {"h1": h1, "h2": h2}

        if detect_max_elephant(h1, h2):
            return "max_elephant", {"h1": h1, "h2": h2}

        if detect_rabbit_escape(h1, h2):
            return "rabbit_escape", {"h1": h1, "h2": h2}

        if detect_nue(h1, h2):
            return "nue", {"h1": h1, "h2": h2}

        if detect_divine_dogs(h1, h2):
            return "divine_dogs", {"h1": h1, "h2": h2}

    if num_hands >= 1:
        # --- Gojo: Técnicas de 1 mano (alta prioridad) ---
        for hand in hands_list:
            if detect_infinite_void(hand):
                return "infinite_void", {"hand": hand}

            if detect_hollow_purple(hand):
                return "hollow_purple", {"hand": hand}

            if detect_red(hand):
                return "red", {"hand": hand}

        # --- Técnicas de 1 mano (evaluar cada mano) ---
        for hand in hands_list:
            if detect_overtime(hand):
                return "overtime", {"hand": hand}

            if detect_ratio(hand):
                return "ratio", {"hand": hand}

        # Blue (open palm) - lowest priority since it conflicts with many gestures
        for hand in hands_list:
            if detect_blue(hand):
                return "blue", {"hand": hand}

    return None, None
