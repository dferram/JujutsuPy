import cv2
import mediapipe as mp
import time
from utils.math_helpers import calculate_euclidean_distance, get_centroid
from core.effects import EffectGenerator

class CursedVision:
    """
    Controlador central de la tubería de AI y Machine Vision. 
    """
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Fallo en la captura de vídeo. Verifica la cámara en el índice {camera_index}.")
        
        # Inicialización de ML MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,             
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.effect_gen = EffectGenerator()
        
        self.charge_frames = 0
        self.ACTIVATION_THRESHOLD = 8 
        self.is_active = False

    def is_divine_dogs_gesture(self, hand_landmarks1, hand_landmarks2):
        """
        Verifica el cruce de manos simulando el Hand Sign de Fushiguro.
        """
        w1 = (hand_landmarks1.landmark[0].x, hand_landmarks1.landmark[0].y) 
        i1 = (hand_landmarks1.landmark[8].x, hand_landmarks1.landmark[8].y) 
        w2 = (hand_landmarks2.landmark[0].x, hand_landmarks2.landmark[0].y) 
        i2 = (hand_landmarks2.landmark[8].x, hand_landmarks2.landmark[8].y) 
        
        dist_wrists = calculate_euclidean_distance(w1, w2)
        dist_indices = calculate_euclidean_distance(i1, i2)
        
        if dist_wrists < 0.3 and dist_indices < 0.15:
            return True
        return False

    def run(self):
        print("🔮 Iniciando Cursed Vision Engine... Presiona 'q' en la ventana para salir.")
        prev_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ [Error] Leyendo frame de la cámara. Saliendo...")
                break
                
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False 
            results = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            gesture_detected = False
            centroid_x, centroid_y = w // 2, h // 2

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(40, 40, 40), thickness=2, circle_radius=2),
                        self.mp_draw.DrawingSpec(color=(128, 0, 128), thickness=2, circle_radius=3)
                    )
                
                if len(results.multi_hand_landmarks) == 2:
                    h1, h2 = results.multi_hand_landmarks[0], results.multi_hand_landmarks[1]
                    if self.is_divine_dogs_gesture(h1, h2):
                        gesture_detected = True
                        centroid_x, centroid_y = get_centroid(h1, h2, w, h)

            if gesture_detected:
                self.charge_frames += 1
                if self.charge_frames < self.ACTIVATION_THRESHOLD:
                    cv2.putText(frame, "Cargando Energia Maldita...", (30, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                else:
                    self.is_active = True
                    cv2.putText(frame, "TECNICA DE SOMBRAS: LOBOS DE JADE", (30, 60), 
                                cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 0, 255), 2)
                    self.effect_gen.draw_divine_dogs(frame, centroid_x, centroid_y, scale=130)
            else:
                self.charge_frames = max(0, self.charge_frames - 2) 
                if self.charge_frames == 0:
                    self.is_active = False

            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (w - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("JujutsuPy Vision Engine", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
