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
from core.hud import CursedEnergySystem, draw_hud
from core.physics import PhysicsParticleSystem


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
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.hand_landmarker = HandLandmarker.create_from_options(options)

        # Para dibujar las conexiones de la mano
        self.hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
        self.draw_utils = mp.tasks.vision.drawing_utils

        # Subsistemas
        self.effect_gen = EffectGenerator()
        self.energy = CursedEnergySystem(max_energy=100.0)
        self.physics = PhysicsParticleSystem(max_particles=300)

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

        elif technique_id == "orochi":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_orochi(frame, cx, cy, fh)

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

        # --- GOJO ---
        elif technique_id == "infinite_void":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_infinite_void(frame, cx, cy, fw, fh)

        elif technique_id == "blue":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_blue_attraction(frame, cx, cy, self.physics, fw, fh)

        elif technique_id == "red":
            cx, cy = get_single_hand_center(hand_data["hand"], fw, fh)
            self.effect_gen.draw_red_repulsion(frame, cx, cy, self.physics, fw, fh)

        elif technique_id == "hollow_purple":
            cx, cy = get_centroid(hand_data["h1"], hand_data["h2"], fw, fh, offset_y=0)
            self.effect_gen.draw_hollow_purple(frame, cx, cy, self.physics, fw, fh)

    def _draw_hand_wireframe(self, frame, hand_landmarks, fw, fh):
        """Dibuja las conexiones y landmarks de una mano manualmente."""
        points = {}
        for idx, lm in enumerate(hand_landmarks.landmark):
            px, py = int(lm.x * fw), int(lm.y * fh)
            points[idx] = (px, py)
            cv2.circle(frame, (px, py), 3, (128, 0, 128), -1)

        # Dibujar conexiones
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),       # Pulgar
            (0, 5), (5, 6), (6, 7), (7, 8),       # Indice
            (0, 17), (5, 9), (9, 13), (13, 17),   # Palma
            (9, 10), (10, 11), (11, 12),           # Medio
            (13, 14), (14, 15), (15, 16),          # Anular
            (17, 18), (18, 19), (19, 20),          # Menique
        ]
        for c1, c2 in connections:
            if c1 in points and c2 in points:
                cv2.line(frame, points[c1], points[c2], (40, 40, 40), 2)

    def run(self):
        """Bucle principal de captura y procesamiento en tiempo real."""
        print("Iniciando JujutsuPy Vision Engine...")
        print("16 Gestos: Gojo (Void/Blue/Red/Purple), Megumi (Dogs/Nue/Orochi/")
        print("   Toad/Elephant/Rabbit/Mahoraga), Nanami (Overtime/Ratio),")
        print("   Higuruma (Gavel), Yuta (Rika/Domain)")
        print("   Presiona 'q' en la ventana para salir.\n")

        prev_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Error] Leyendo frame de la camara. Saliendo...")
                break

            frame = cv2.flip(frame, 1)
            fh, fw = frame.shape[:2]

            # Convertir frame a mp.Image para la nueva API
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Timestamp incremental (la API VIDEO requiere timestamps crecientes)
            self._frame_timestamp_ms += 33  # ~30fps
            result = self.hand_landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

            # Convertir resultado a formato compatible con nuestros gestores
            hands_list = []
            if result.hand_landmarks:
                for hand_lms in result.hand_landmarks:
                    wrapper = _LandmarkListWrapper(hand_lms)
                    hands_list.append(wrapper)
                    self._draw_hand_wireframe(frame, wrapper, fw, fh)

            # Deteccion de gesto activo
            technique_id, hand_data = detect_active_technique(hands_list)

            technique_detected = technique_id is not None and self.energy.has_energy()

            if technique_detected:
                self.charge_frames += 1
                if self.charge_frames >= self.ACTIVATION_THRESHOLD:
                    self.current_technique = technique_id
                    info = TECHNIQUE_INFO.get(technique_id, ("UNKNOWN", "???"))
                    tech_name, character = info

                    # Renderizar efecto visual
                    self._render_effect(frame, technique_id, hand_data, fw, fh)

                    # Actualizar energia (gastando)
                    self.energy.update(is_active=True)

                    # HUD con tecnica activa
                    draw_hud(frame, self.energy, tech_name, character)
                else:
                    # Estado: Cargando
                    self.energy.update(is_active=False)
                    draw_hud(frame, self.energy)
                    cv2.putText(frame, "Cargando Energia Maldita...", (30, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            else:
                # Sin gesto: decaimiento y regeneracion
                self.charge_frames = max(0, self.charge_frames - 2)
                if self.charge_frames == 0:
                    self.current_technique = None
                self.energy.update(is_active=False)
                draw_hud(frame, self.energy)

            # FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (fw - 100, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("JujutsuPy Vision Engine", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.hand_landmarker.close()
        self.cap.release()
        cv2.destroyAllWindows()
