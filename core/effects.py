import cv2
import numpy as np
import random

class EffectGenerator:
    """
    Clase encargada de renderizar los efectos visuales (Energía Maldita y Shikigamis).
    """
    def __init__(self):
        # Generar las coordenadas del lobo una sola vez durante la inicialización
        self.wolf_points = self._generate_wolf_silhouette()
        self.particle_color = (128, 0, 128) # Morado neón oscuro (BGR) en OpenCV
        self.glow_color = (200, 50, 200)    # Resplandor morado más claro
        
    def _generate_wolf_silhouette(self):
        """
        Genera la silueta matemática de los 'Divine Dogs'.
        Retorna una lista de tuplas (x, y) relativas normalizadas.
        """
        return [
            (0.0, -0.8),    # Punta oreja izquierda
            (0.2, -0.4),    # Base oreja izquierda
            (0.5, -0.9),    # Punta oreja derecha
            (0.4, -0.3),    # Base oreja derecha
            (0.6, -0.1),    # Frente
            (0.9, 0.2),     # Hocico superior
            (1.0, 0.4),     # Punta de la nariz
            (0.8, 0.5),     # Mandíbula superior
            (0.7, 0.7),     # Boca inferior
            (0.4, 0.8),     # Cuello frontal
            (-0.3, 0.9),    # Base del cuello/pecho
            (-0.6, 0.5),    # Nuca
            (-0.5, 0.0),    # Parte trasera de la cabeza
            (-0.2, -0.3)    # Retorno a oreja izquierda
        ]
        
    def draw_divine_dogs(self, frame, center_x, center_y, scale=130):
        """
        Renderiza la silueta del Shikigami interpolando vértices y utilizando
        un sistema de partículas con 'jitter' (movimiento fluido estocástico).
        """
        num_particles_per_segment = 20
        all_particles = []
        
        # Interpolación lineal
        for i in range(len(self.wolf_points)):
            p1 = self.wolf_points[i]
            p2 = self.wolf_points[(i + 1) % len(self.wolf_points)]
            
            for t in np.linspace(0, 1, num_particles_per_segment):
                x = p1[0] + (p2[0] - p1[0]) * t
                y = p1[1] + (p2[1] - p1[1]) * t
                all_particles.append((x, y))
                
        # Dibujar sistema dinámico de puntos
        for (nx, ny) in all_particles:
            jitter_x = random.randint(-4, 4)
            jitter_y = random.randint(-4, 4)
            
            px = int(center_x + nx * scale + jitter_x)
            py = int(center_y + ny * scale + jitter_y)
            
            if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                cv2.circle(frame, (px, py), 2, self.particle_color, -1)
                
                if random.random() > 0.85:
                    cv2.circle(frame, (px, py), 6, self.glow_color, 1)
