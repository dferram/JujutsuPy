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
    Divine Dog (Ken): Palmas unidas lateralmente, pulgares arriba.
    Firma: Muñecas cercanas (< 0.3) + Índices cercanos (< 0.15).
    """
    w1, w2 = landmarks_to_point(h1, 0), landmarks_to_point(h2, 0)
    i1, i2 = landmarks_to_point(h1, 8), landmarks_to_point(h2, 8)

    dist_wrists = calculate_euclidean_distance(w1, w2)
    dist_indices = calculate_euclidean_distance(i1, i2)

    return dist_wrists < 0.3 and dist_indices < 0.15


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


def detect_orochi(hand):
    """
    Great Serpent (Orochi): Mano derecha alzada, dedos juntos, pulgar recogido.
    Firma: Todas las puntas cercanas entre sí + pulgar no extendido.
    Requiere 1 sola mano.
    """
    tips = [landmarks_to_point(hand, i) for i in [8, 12, 16, 20]]

    # Verificar que las puntas están agrupadas (juntas)
    max_dist = 0
    for i in range(len(tips)):
        for j in range(i + 1, len(tips)):
            d = calculate_euclidean_distance(tips[i], tips[j])
            if d > max_dist:
                max_dist = d

    # Dedos muy juntos y pulgar recogido
    return max_dist < 0.08 and not is_thumb_extended(hand)


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
    Mahoraga (Eight-Handled Sword): Puntas de los dedos tocándose en círculo.
    Firma: Los 5 pares de puntas de dedos correspondientes están muy cercanos (< 0.06).
    """
    tip_ids = [4, 8, 12, 16, 20]
    close_pairs = 0

    for tid in tip_ids:
        p1 = landmarks_to_point(h1, tid)
        p2 = landmarks_to_point(h2, tid)
        if calculate_euclidean_distance(p1, p2) < 0.06:
            close_pairs += 1

    # Al menos 4 de 5 pares deben estar tocándose
    return close_pairs >= 4


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


# =============================================================================
#  HIGURUMA HIROMI — Deadly Sentencing (1 técnica)
# =============================================================================

def detect_gavel_strike(h1, h2):
    """
    Gavel Strike: Puño derecho golpeando la palma izquierda.
    Firma: Muñeca de h1 (0) cerca del centro de palma de h2 (9) o viceversa (< 0.07).
    """
    w1 = landmarks_to_point(h1, 0)
    p2 = landmarks_to_point(h2, 9)
    w2 = landmarks_to_point(h2, 0)
    p1 = landmarks_to_point(h1, 9)

    d1 = calculate_euclidean_distance(w1, p2)
    d2 = calculate_euclidean_distance(w2, p1)

    # Cualquiera de las dos manos puede ser el puño
    return d1 < 0.07 or d2 < 0.07


# =============================================================================
#  YUTA OKKOTSU — Pure Love (2 técnicas)
# =============================================================================

def detect_rika(hand):
    """
    Rika Manifestation: Besar el anillo — pulgar (4) cerca de la boca.
    Firma: Thumb tip (4) en zona Y < 0.35 (parte alta de la cámara, zona de rostro).
    Se asume que el usuario tiene la mano izquierda cerca de la cara.
    """
    thumb_tip = hand.landmark[4]
    index_tip = hand.landmark[8]

    # Mano cerca de la cara (zona alta)
    if thumb_tip.y > 0.40:
        return False

    # Pulgar e índice se tocan (simulación de besar el anillo)
    dist = calculate_euclidean_distance(
        (thumb_tip.x, thumb_tip.y),
        (index_tip.x, index_tip.y)
    )

    return dist < 0.05


def detect_domain_yuta(h1, h2):
    """
    Domain Expansion (Authentic Mutual Love): Manos entrelazadas complejas
    frente al rostro, índices cruzados apuntando arriba.
    Firma: Palmas cercanas + índices extendidos + cruzados en X + posición alta.
    """
    p1, p2 = landmarks_to_point(h1, 9), landmarks_to_point(h2, 9)
    if calculate_euclidean_distance(p1, p2) > 0.15:
        return False

    # Índices extendidos
    if not (is_finger_extended(h1, 8, 6) and is_finger_extended(h2, 8, 6)):
        return False

    # Índices cruzados: las X de los tips deben invertirse respecto a sus bases
    i1_tip = h1.landmark[8]
    i2_tip = h2.landmark[8]

    # Posición alta (frente al rostro)
    if i1_tip.y > 0.45 or i2_tip.y > 0.45:
        return False

    return True


# =============================================================================
#  DISPATCHER PRINCIPAL — Máquina de Detección Multi-Técnica
# =============================================================================

# Mapeo: ID → (nombre_display, character)
TECHNIQUE_INFO = {
    "divine_dogs":    ("DIVINE DOGS: KEN", "Megumi"),
    "nue":            ("NUE: THUNDERBIRD", "Megumi"),
    "orochi":         ("GREAT SERPENT: OROCHI", "Megumi"),
    "toad":           ("TOAD: GAMA", "Megumi"),
    "max_elephant":   ("MAX ELEPHANT", "Megumi"),
    "rabbit_escape":  ("RABBIT ESCAPE", "Megumi"),
    "mahoraga":       ("MAHORAGA: EIGHT-HANDLED SWORD", "Megumi"),
    "overtime":       ("OVERTIME MODE", "Nanami"),
    "ratio":          ("RATIO TECHNIQUE: 7:3", "Nanami"),
    "gavel_strike":   ("GAVEL STRIKE: DEADLY SENTENCING", "Higuruma"),
    "rika":           ("RIKA: MANIFESTATION", "Yuta"),
    "domain_yuta":    ("DOMAIN: AUTHENTIC MUTUAL LOVE", "Yuta"),
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

        if detect_gavel_strike(h1, h2):
            return "gavel_strike", {"h1": h1, "h2": h2}

        if detect_domain_yuta(h1, h2):
            return "domain_yuta", {"h1": h1, "h2": h2}

        if detect_toad(h1, h2):
            return "toad", {"h1": h1, "h2": h2}

        if detect_max_elephant(h1, h2):
            return "max_elephant", {"h1": h1, "h2": h2}

        if detect_rabbit_escape(h1, h2):
            return "rabbit_escape", {"h1": h1, "h2": h2}

        if detect_nue(h1, h2):
            return "nue", {"h1": h1, "h2": h2}

        if detect_divine_dogs(h1, h2):
            return "divine_dogs", {"h1": h1, "h2": h2}

    if num_hands >= 1:
        # --- Técnicas de 1 mano (evaluar cada mano) ---
        for hand in hands_list:
            if detect_rika(hand):
                return "rika", {"hand": hand}

            if detect_overtime(hand):
                return "overtime", {"hand": hand}

            if detect_ratio(hand):
                return "ratio", {"hand": hand}

            if detect_orochi(hand):
                return "orochi", {"hand": hand}

    return None, None
