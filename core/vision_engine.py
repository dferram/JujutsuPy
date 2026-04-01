"""
core/vision_engine.py — Motor Central de Computer Vision

Orquesta la captura de cámara, la detección de gestos con MediaPipe,
el renderizado de efectos visuales, y el HUD de Energía Maldita.
"""

import cv2
import mediapipe as mp
import time

from utils.math_helpers import get_centroid, get_single_hand_center
from core.effects import EffectGenerator
from core.gestures import detect_active_technique, TECHNIQUE_INFO
from core.hud import CursedEnergySystem, draw_hud


class CursedVision:
    """
    Controlador central de la tubería de AI y Machine Vision.
    Implementa una Máquina de Estados Finita multi-técnica.
    """
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Fallo en la captura de vídeo. Verifica la cámara en el índice {camera_index}."
            )

        # MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Subsistemas
        self.effect_gen = EffectGenerator()
        self.energy = CursedEnergySystem(max_energy=100.0)

        # Estado de carga universal
        self.charge_frames = 0
        self.ACTIVATION_THRESHOLD = 8
        self.current_technique = None

    def _render_effect(self, frame, technique_id, hand_data, fw, fh):
        """Delega el renderizado al método correcto del EffectGenerator."""

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

    def run(self):
        """Bucle principal de captura y procesamiento en tiempo real."""
        print("🔮 Iniciando JujutsuPy Vision Engine...")
        print("📜 Gestos disponibles: Divine Dogs, Nue, Orochi, Toad, Max Elephant,")
        print("   Rabbit Escape, Mahoraga, Overtime, Ratio 7:3, Gavel Strike, Rika, Domain")
        print("   Presiona 'q' en la ventana para salir.\n")

        prev_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ [Error] Leyendo frame de la cámara. Saliendo...")
                break

            frame = cv2.flip(frame, 1)
            fh, fw = frame.shape[:2]

            # Pipeline MediaPipe (optimización: flag de escritura)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            # Dibujar wireframe de las manos detectadas
            hands_list = results.multi_hand_landmarks or []
            for hand_lm in hands_list:
                self.mp_draw.draw_landmarks(
                    frame, hand_lm, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(40, 40, 40), thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=(128, 0, 128), thickness=2, circle_radius=3)
                )

            # Detección de gesto activo
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

                    # Actualizar energía (gastando)
                    self.energy.update(is_active=True)

                    # HUD con técnica activa
                    draw_hud(frame, self.energy, tech_name, character)
                else:
                    # Estado: Cargando
                    self.energy.update(is_active=False)
                    draw_hud(frame, self.energy)
                    cv2.putText(frame, "Cargando Energia Maldita...", (30, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            else:
                # Sin gesto: decaimiento y regeneración
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

        self.cap.release()
        cv2.destroyAllWindows()
