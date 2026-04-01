"""
core/vision_engine.py — Motor Central de Computer Vision

Orquesta la captura de camara, la deteccion de gestos con MediaPipe,
el renderizado de efectos visuales, y el HUD de Energia Maldita.

Usa la API de tareas de MediaPipe (mp.tasks.vision.HandLandmarker)
compatible con mediapipe >= 0.10.30.
"""

import cv2
import mediapipe as mp
import time
import os

from utils.math_helpers import get_centroid, get_single_hand_center
from core.effects import EffectGenerator
from core.gestures import detect_active_technique, TECHNIQUE_INFO
from core.hud import CursedEnergySystem
from core.physics import PhysicsParticleSystem
from core.renderer import CinematicRenderer


# =========================================================================
#  EMA (Exponential Moving Average) Landmark Smoother
# =========================================================================
class LandmarkSmoother:
    """Suavizador de tracking para eliminar el jitter de MediaPipe."""
    def __init__(self, alpha=0.6):
        self.alpha = alpha
        self.history = {}

    def smooth(self, current_hands_landmarks):
        smoothed_hands = []
        for i, hand in enumerate(current_hands_landmarks):
            smoothed_hand = []
            if i in self.history and len(self.history[i]) == len(hand):
                # Filtro EMA (Promedio Móvil Exponencial)
                for curr, prev in zip(hand, self.history[i]):
                    curr.x = self.alpha * curr.x + (1 - self.alpha) * prev.x
                    curr.y = self.alpha * curr.y + (1 - self.alpha) * prev.y
                    curr.z = self.alpha * curr.z + (1 - self.alpha) * prev.z
                    smoothed_hand.append(curr)
            else:
                smoothed_hand = hand
            
            import copy
            self.history[i] = copy.deepcopy(smoothed_hand)
            smoothed_hands.append(smoothed_hand)
            
        keys_to_remove = [k for k in self.history if k >= len(current_hands_landmarks)]
        for k in keys_to_remove:
            del self.history[k]
                
        return smoothed_hands


# Adaptador: la nueva API retorna NormalizedLandmark objects
# pero nuestros gestures.py esperan objetos con .landmark[i].x/.y
# Este wrapper mantiene compatibilidad sin tocar el resto del código
class _LandmarkListWrapper:
    """Envuelve una lista de NormalizedLandmark para imitar la interfaz legacy."""
    def __init__(self, landmark_list):
        self.landmark = landmark_list


class CursedVision:
    """
    Controlador central de la tuberia de AI y Machine Vision.
    Implementa una Maquina de Estados Finita multi-tecnica.
    """
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Fallo en la captura de video. Verifica la camara en el indice {camera_index}."
            )

        # Ruta al modelo de HandLandmarker
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models", "hand_landmarker.task"
        )
        if not os.path.exists(model_path):
            raise RuntimeError(
                f"Modelo no encontrado en {model_path}. "
                "Descargalo de: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )

        # Inicializar HandLandmarker (nueva API basada en tareas)
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.85,
            min_hand_presence_confidence=0.85,
            min_tracking_confidence=0.85,
        )
        self.hand_landmarker = HandLandmarker.create_from_options(options)
        self.smoother = LandmarkSmoother(alpha=0.65)

        # Para dibujar las conexiones de la mano
        self.hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
        self.draw_utils = mp.tasks.vision.drawing_utils

        # Subsistemas
        self.effect_gen = EffectGenerator()
        self.energy = CursedEnergySystem(max_energy=100.0)
        self.physics = PhysicsParticleSystem(max_particles=300)
        self.renderer = CinematicRenderer(1920, 1080)

        # Estado de carga universal
        self.charge_frames = 0
        self.ACTIVATION_THRESHOLD = 8
        self.current_technique = None

        # Timestamp para la API de video
        self._frame_timestamp_ms = 0

    def _render_effect(self, frame, technique_id, hand_data, fw, fh):
        """Delega el renderizado al metodo correcto del EffectGenerator."""

        # --- MEGUMI ---
        if technique_id == "divine_dogs":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh)
            self.effect_gen.draw_divine_dogs(frame, cx, cy)

        elif technique_id == "nue":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=-120)
            self.effect_gen.draw_nue(frame, cx, cy)

        elif technique_id == "toad":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=0)
            self.effect_gen.draw_toad(frame, cx, cy, fw, fh)

        elif technique_id == "max_elephant":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=0)
            self.effect_gen.draw_max_elephant(frame, cx, cy, fw)

        elif technique_id == "rabbit_escape":
            self.effect_gen.draw_rabbit_escape(frame, fw, fh)

        elif technique_id == "mahoraga":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=-100)
            self.effect_gen.draw_mahoraga_wheel(frame, cx, cy)

        # --- NANAMI ---
        elif technique_id == "overtime":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_overtime_aura(frame, cx, cy)

        elif technique_id == "ratio":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_ratio_line(frame, cx, cy)

        # --- HIGURUMA ---
        elif technique_id == "gavel_strike":
            self.effect_gen.draw_gavel_impact(frame, fw, fh)

        # --- YUTA ---
        elif technique_id == "rika":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_rika(frame, cx, cy - 100)

        elif technique_id == "domain_yuta":
            self.effect_gen.draw_sword_rain(frame, fw, fh)
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=-60)
            self.effect_gen.draw_rika(frame, cx, cy, scale=120)

        # --- GOJO (Hardcoded a pantalla completa en el centro) ---
        elif technique_id == "infinite_void":
            cx, cy = fw // 2, fh // 2
            self.effect_gen.draw_infinite_void(frame, cx, cy, fw, fh)

        elif technique_id == "blue":
            cx, cy = fw // 2, fh // 2
            self.effect_gen.draw_blue_attraction(frame, cx, cy, self.physics, fw, fh)

        elif technique_id == "red":
            cx, cy = fw // 2, fh // 2
            self.effect_gen.draw_red_repulsion(frame, cx, cy, self.physics, fw, fh)

        elif technique_id == "hollow_purple":
            cx, cy = fw // 2, fh // 2
            self.effect_gen.draw_hollow_purple(frame, cx, cy, self.physics, fw, fh)

    def run(self):
        """Bucle principal de captura y procesamiento en tiempo real."""
        print("Iniciando JujutsuPy Cinematic Vision Engine...")
        print("Pantalla completa activa. Presiona 'q' para salir.\n")

        # Configurar pantalla completa
        cv2.namedWindow("JujutsuPy Vision Engine", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("JujutsuPy Vision Engine", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        prev_time = time.time()

        while True:
            ret, cam_frame = self.cap.read()
            if not ret:
                break

            cam_frame = cv2.flip(cam_frame, 1)

            # Convertir frame a mp.Image para MediaPipe
            rgb_frame = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            self._frame_timestamp_ms += 33
            result = self.hand_landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

            # Calcular FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
            prev_time = curr_time

            # Preparamos el CANVAS gigante
            canvas = self.renderer.create_canvas()
            self.renderer.draw_background(canvas)
            cw, ch = self.renderer.W, self.renderer.H

            # Convertir wrappers y suavizar landmarks
            hands_list = []
            if result.hand_landmarks:
                smoothed_landmarks = self.smoother.smooth(result.hand_landmarks)
                for hand_lms in smoothed_landmarks:
                    hands_list.append(_LandmarkListWrapper(hand_lms))

            technique_id, hand_data = detect_active_technique(hands_list)
            technique_detected = technique_id is not None and self.energy.has_energy()

            tech_name, character = None, None
            is_active = False

            if technique_detected:
                self.charge_frames += 1
                if self.charge_frames >= self.ACTIVATION_THRESHOLD:
                    is_active = True
                    self.current_technique = technique_id
                    tech_name, character = TECHNIQUE_INFO.get(technique_id, ("UNKNOWN", "???"))

                    # Renderizamos efectos sobre el CANVAS (al tamaño gigante)
                    self._render_effect(canvas, technique_id, hand_data, cw, ch)
                    self.energy.update(is_active=True)
                else:
                    self.energy.update(is_active=False)
            else:
                self.charge_frames = max(0, self.charge_frames - 2)
                if self.charge_frames == 0:
                    self.current_technique = None
                self.energy.update(is_active=False)

            # Dibujar la camara en la esquina (el inset se encarga internamente de dibujar los neones de la mano)
            self.renderer.draw_webcam_inset(canvas, cam_frame, hands_list)

            # Dibujar el HUD cinematográfico
            self.renderer.draw_professional_hud(canvas, self.energy, fps, tech_name, character, is_active)

            cv2.imshow("JujutsuPy Vision Engine", canvas)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.hand_landmarker.close()
        self.cap.release()
        cv2.destroyAllWindows()
