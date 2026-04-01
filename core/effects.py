"""
core/effects.py — Motor de Efectos Visuales (Partículas y Renderizado)

Cada método renderiza un efecto de Energía Maldita específico para una técnica.
Todos los efectos usan la misma base de partículas interpoladas con jitter pero
difieren en silueta, color, y comportamiento dinámico.
"""

import cv2
import numpy as np
import random
import math
import time


class EffectGenerator:
    """
    Generador de efectos visuales para todas las técnicas de Jujutsu.
    """
    def __init__(self):
        # Pre-computar siluetas estáticas una sola vez
        self._wolf_points = self._gen_wolf()
        self._nue_points = self._gen_nue()
        self._serpent_phase = 0.0
        self._wheel_angle = 0.0
        self._rabbit_particles = [(random.random(), random.random()) for _ in range(200)]
        self._sword_particles = [(random.uniform(0.1, 0.9), random.uniform(-0.3, 0.0)) for _ in range(40)]
        self._gavel_flash = 0
        self._void_angle = 0.0
        self._purple_trail = []  # Estela de Hollow Purple

    # =========================================================================
    #  GENERADORES DE SILUETAS (Coordenadas matemáticas relativas)
    # =========================================================================

    @staticmethod
    def _gen_wolf():
        return [
            (0.0, -0.8), (0.2, -0.4), (0.5, -0.9), (0.4, -0.3),
            (0.6, -0.1), (0.9, 0.2), (1.0, 0.4), (0.8, 0.5),
            (0.7, 0.7), (0.4, 0.8), (-0.3, 0.9), (-0.6, 0.5),
            (-0.5, 0.0), (-0.2, -0.3)
        ]

    @staticmethod
    def _gen_nue():
        """Silueta de un búho/ave con alas extendidas."""
        return [
            # Ala izquierda
            (-1.2, 0.0), (-1.0, -0.3), (-0.7, -0.5), (-0.4, -0.3),
            # Cabeza
            (-0.2, -0.6), (0.0, -0.8), (0.2, -0.6),
            # Ala derecha
            (0.4, -0.3), (0.7, -0.5), (1.0, -0.3), (1.2, 0.0),
            # Cola/cuerpo inferior
            (0.8, 0.3), (0.3, 0.5), (0.0, 0.6), (-0.3, 0.5), (-0.8, 0.3),
        ]

    # =========================================================================
    #  UTILIDAD: Interpolación + Jitter (Reutilizable)
    # =========================================================================

    def _draw_silhouette_particles(self, frame, points, cx, cy, scale,
                                    color, glow_color, jitter=4,
                                    particles_per_seg=18, dot_size=2,
                                    glow_chance=0.15, glow_radius=6):
        """Método base para renderizar cualquier silueta como sistema de partículas."""
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]

            for t in np.linspace(0, 1, particles_per_seg):
                x = p1[0] + (p2[0] - p1[0]) * t
                y = p1[1] + (p2[1] - p1[1]) * t

                jx = random.randint(-jitter, jitter)
                jy = random.randint(-jitter, jitter)

                px = int(cx + x * scale + jx)
                py = int(cy + y * scale + jy)

                if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                    cv2.circle(frame, (px, py), dot_size, color, -1)
                    if random.random() < glow_chance:
                        cv2.circle(frame, (px, py), glow_radius, glow_color, 1)

    # =========================================================================
    #  MEGUMI FUSHIGURO
    # =========================================================================

    def draw_divine_dogs(self, frame, cx, cy, scale=130):
        """Lobo de puntos morados oscuros con glow pasivo."""
        self._draw_silhouette_particles(
            frame, self._wolf_points, cx, cy, scale,
            color=(128, 0, 128), glow_color=(200, 50, 200)
        )

    def draw_nue(self, frame, cx, cy, scale=110):
        """Alas de partículas eléctricas cyan/blancas."""
        self._draw_silhouette_particles(
            frame, self._nue_points, cx, cy, scale,
            color=(230, 230, 50), glow_color=(255, 255, 200),
            jitter=5, glow_chance=0.25
        )
        # Chispa eléctrica: líneas aleatorias entre puntos cercanos
        for _ in range(8):
            x1 = cx + random.randint(-int(scale * 1.2), int(scale * 1.2))
            y1 = cy + random.randint(-int(scale * 0.8), int(scale * 0.5))
            x2 = x1 + random.randint(-25, 25)
            y2 = y1 + random.randint(-25, 25)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 100), 1)

    def draw_orochi(self, frame, hand_cx, hand_cy, frame_h, scale=1.0):
        """Serpiente: línea sinusoidal de puntos verdes que sube desde abajo hasta la mano."""
        self._serpent_phase += 0.15
        num_points = 80
        for i in range(num_points):
            t = i / num_points
            # Movimiento de abajo hacia la mano
            y = int(frame_h - t * (frame_h - hand_cy))
            x_wave = math.sin(t * 6 * math.pi + self._serpent_phase) * 40 * scale
            x = int(hand_cx + x_wave)

            if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                jx = random.randint(-3, 3)
                jy = random.randint(-3, 3)
                cv2.circle(frame, (x + jx, y + jy), 3, (0, 180, 0), -1)
                if random.random() < 0.2:
                    cv2.circle(frame, (x, y), 7, (0, 255, 80), 1)

        # Cabeza de serpiente
        cv2.circle(frame, (hand_cx, hand_cy), 8, (0, 255, 0), -1)

    def draw_toad(self, frame, cx, cy, fw, fh):
        """Lenguas de partículas verdes lanzándose hacia los bordes."""
        targets = [(0, cy), (fw, cy), (cx, 0), (cx, fh)]
        for tx, ty in targets:
            num_dots = 30
            for i in range(num_dots):
                t = i / num_dots
                x = int(cx + (tx - cx) * t)
                y = int(cy + (ty - cy) * t)

                # Solo dibuja la parte cercana (lengua corta)
                if t > 0.4:
                    break

                jx = random.randint(-5, 5)
                jy = random.randint(-5, 5)
                if 0 <= x + jx < frame.shape[1] and 0 <= y + jy < frame.shape[0]:
                    cv2.circle(frame, (x + jx, y + jy), 3, (30, 200, 30), -1)

    def draw_max_elephant(self, frame, cx, cy, fw):
        """Cascada de partículas de agua cayendo desde arriba."""
        for _ in range(60):
            x = cx + random.randint(-150, 150)
            y = random.randint(0, cy)
            jx = random.randint(-3, 3)

            if 0 <= x + jx < frame.shape[1] and 0 <= y < frame.shape[0]:
                # Partículas azules tipo agua
                size = random.randint(2, 5)
                cv2.circle(frame, (x + jx, y), size, (200, 150, 50), -1)
                if random.random() < 0.3:
                    cv2.circle(frame, (x + jx, y), size + 4, (230, 200, 100), 1)

    def draw_rabbit_escape(self, frame, fw, fh):
        """Cientos de puntos blancos frenéticos por toda la cámara."""
        for i in range(len(self._rabbit_particles)):
            rx, ry = self._rabbit_particles[i]
            # Movimiento caótico
            rx += random.uniform(-0.03, 0.03)
            ry += random.uniform(-0.03, 0.03)
            rx = rx % 1.0
            ry = ry % 1.0
            self._rabbit_particles[i] = (rx, ry)

            px = int(rx * fw)
            py = int(ry * fh)
            if 0 <= px < fw and 0 <= py < fh:
                cv2.circle(frame, (px, py), 2, (240, 240, 240), -1)
                if random.random() < 0.1:
                    cv2.circle(frame, (px, py), 5, (255, 255, 255), 1)

    def draw_mahoraga_wheel(self, frame, cx, cy, scale=150):
        """Rueda de 8 radios dorados girando detrás del usuario."""
        self._wheel_angle += 0.04  # Velocidad de rotación

        # Dibujar el anillo exterior
        for i in range(80):
            angle = (i / 80) * 2 * math.pi + self._wheel_angle
            x = int(cx + math.cos(angle) * scale)
            y = int(cy + math.sin(angle) * scale)
            jx = random.randint(-2, 2)
            jy = random.randint(-2, 2)
            if 0 <= x + jx < frame.shape[1] and 0 <= y + jy < frame.shape[0]:
                cv2.circle(frame, (x + jx, y + jy), 2, (0, 200, 255), -1)

        # Dibujar los 8 radios
        for spoke in range(8):
            angle = (spoke / 8) * 2 * math.pi + self._wheel_angle
            for r in range(10, int(scale), 8):
                x = int(cx + math.cos(angle) * r)
                y = int(cy + math.sin(angle) * r)
                jx = random.randint(-2, 2)
                jy = random.randint(-2, 2)
                if 0 <= x + jx < frame.shape[1] and 0 <= y + jy < frame.shape[0]:
                    cv2.circle(frame, (x + jx, y + jy), 2, (0, 215, 255), -1)
                    if random.random() < 0.15:
                        cv2.circle(frame, (x, y), 5, (50, 235, 255), 1)

    # =========================================================================
    #  KENTO NANAMI
    # =========================================================================

    def draw_overtime_aura(self, frame, cx, cy, scale=80):
        """Aura de partículas amarillas densas rodeando el puño + reloj digital."""
        # Aura circular densa
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(scale * 0.5, scale * 1.2)
            x = int(cx + math.cos(angle) * r)
            y = int(cy + math.sin(angle) * r)

            if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                cv2.circle(frame, (x, y), 2, (0, 220, 255), -1)
                if random.random() < 0.2:
                    cv2.circle(frame, (x, y), 6, (50, 255, 255), 1)

        # Reloj digital en la esquina
        clock_str = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"OVERTIME {clock_str}", (frame.shape[1] - 300, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

    def draw_ratio_line(self, frame, cx, cy, length=200):
        """Línea de energía azul con punto 70% brillante 'CRITICAL HIT'."""
        # Línea base azul
        x_start = cx - length // 2
        x_end = cx + length // 2
        cv2.line(frame, (x_start, cy), (x_end, cy), (255, 100, 0), 2)

        # Punto crítico al 70%
        crit_x = int(x_start + length * 0.7)

        # Círculo brillante pulsante
        pulse = int(8 + 4 * math.sin(time.time() * 8))
        cv2.circle(frame, (crit_x, cy), pulse, (255, 200, 0), -1)
        cv2.circle(frame, (crit_x, cy), pulse + 5, (255, 255, 100), 2)

        # Etiqueta
        cv2.putText(frame, "CRITICAL HIT", (crit_x - 60, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)

        # Partículas de energía a lo largo de la línea
        for _ in range(15):
            x = random.randint(x_start, x_end)
            y = cy + random.randint(-15, 15)
            if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                cv2.circle(frame, (x, y), 2, (255, 150, 50), -1)

    # =========================================================================
    #  HIGURUMA HIROMI
    # =========================================================================

    def draw_gavel_impact(self, frame, fw, fh):
        """Pantalla oscurecida + platillos de balanza dorados."""
        # Oscurecer el frame
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (fw, fh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        # Rejilla geométrica de juzgado (líneas tenues)
        for x in range(0, fw, 50):
            cv2.line(frame, (x, 0), (x, fh), (30, 30, 50), 1)
        for y in range(0, fh, 50):
            cv2.line(frame, (0, y), (fw, y), (30, 30, 50), 1)

        # Balanza
        center_x = fw // 2
        top_y = 60
        arm_length = 150
        # Barra horizontal
        cv2.line(frame, (center_x - arm_length, top_y),
                 (center_x + arm_length, top_y), (0, 215, 255), 3)
        # Soporte vertical
        cv2.line(frame, (center_x, top_y), (center_x, top_y + 30), (0, 215, 255), 3)

        # Platillos
        for side in [-1, 1]:
            px = center_x + side * arm_length
            # Cadenas
            cv2.line(frame, (px, top_y), (px, top_y + 60), (0, 200, 230), 2)
            # Platillo (semicírculo)
            cv2.ellipse(frame, (px, top_y + 65), (40, 15), 0, 0, 360, (0, 215, 255), 2)

        cv2.putText(frame, "DEADLY SENTENCING", (center_x - 130, fh - 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 215, 255), 2)

    # =========================================================================
    #  YUTA OKKOTSU
    # =========================================================================

    def draw_rika(self, frame, cx, cy, scale=180):
        """Masa gigante de partículas negras y blancas (Rika) detrás del usuario."""
        for _ in range(200):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, scale)
            x = int(cx + math.cos(angle) * r)
            y = int(cy + math.sin(angle) * r - 50)  # ligeramente arriba

            if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                # Mezcla de partículas negras oscuras y blancas fantasmales
                if random.random() < 0.6:
                    color = (30, 0, 30)   # Negro/morado oscuro
                    cv2.circle(frame, (x, y), 3, color, -1)
                else:
                    color = (200, 200, 220)  # Blanco fantasmal
                    cv2.circle(frame, (x, y), 2, color, -1)

                # Ojos rojos de Rika
                if random.random() < 0.02:
                    cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

    def draw_sword_rain(self, frame, fw, fh):
        """Lluvia de espadas de puntos de luz cayendo suavemente."""
        for i in range(len(self._sword_particles)):
            sx, sy = self._sword_particles[i]
            sy += 0.008  # Caída lenta

            if sy > 1.1:
                sy = random.uniform(-0.3, 0.0)
                sx = random.uniform(0.1, 0.9)
            self._sword_particles[i] = (sx, sy)

            px = int(sx * fw)
            py = int(sy * fh)

            if 0 <= px < fw and 0 <= py < fh:
                # Cada "espada" es una línea vertical corta con brillo
                cv2.line(frame, (px, py), (px, py + 15), (200, 200, 255), 2)
                cv2.circle(frame, (px, py), 3, (255, 255, 255), -1)
                if random.random() < 0.1:
                    cv2.circle(frame, (px, py), 6, (220, 220, 255), 1)

    # =========================================================================
    #  SATORU GOJO — Limitless
    # =========================================================================

    def draw_infinite_void(self, frame, cx, cy, fw, fh, scale=300):
        """
        Infinite Void (Anime Quality): Portal masivo en el centro de la pantalla.
        Filamentos entrelazados, anillos rotando, blanco y cian neón.
        """
        self._void_angle += 0.05

        # Oscurecer severamente el fondo
        overlay = np.zeros_like(frame)
        
        # Anillos elípticos de filamentos entrelazados
        for ring in range(5):
            r_base = scale + ring * 40
            pts = 120
            # Dos filamentos en espiral por anillo
            for f in range(2):
                prev_pt = None
                for i in range(pts + 1):
                    # Fase del filamento
                    theta = (i / pts) * 2 * math.pi
                    # Onda senoidal sobre el radio para el efecto de filamento
                    wave = math.sin(theta * 8 + self._void_angle * 3 + f * math.pi) * 30
                    
                    angle = theta + self._void_angle * (1.5 if ring % 2 == 0 else -1.5)
                    
                    # Proyección elíptica
                    x = int(cx + math.cos(angle) * (r_base + wave) * 0.7)
                    y = int(cy + math.sin(angle) * (r_base + wave) * 1.5)
                    
                    if 0 <= x < fw and 0 <= y < fh:
                        if prev_pt:
                            # Cyan brillante / Blanco neón (BGR)
                            color = (255, 255, 255) if f == 0 else (255, 255, 150)
                            thickness = 2 if f == 0 else 4
                            cv2.line(overlay, prev_pt, (x, y), color, thickness)
                        prev_pt = (x, y)
        
        # Centro: Núcleo interior masivo
        cv2.ellipse(overlay, (cx, cy), (int(scale * 0.6), int(scale * 1.3)), 0, 0, 360, (255, 255, 255), 3)
        cv2.ellipse(overlay, (cx, cy), (int(scale * 0.6), int(scale * 1.3)), 0, 0, 360, (255, 255, 100), 10)
        
        # Partículas internas siendo absorbidas
        for _ in range(40):
            r = random.uniform(0, scale * 0.5)
            ang = random.uniform(0, 2*math.pi)
            px = int(cx + math.cos(ang) * r * 0.7)
            py = int(cy + math.sin(ang) * r * 1.5)
            cv2.circle(overlay, (px, py), random.randint(1, 3), (255, 255, 255), -1)

        # Blur y addWeighted para efecto Glow
        glow = cv2.GaussianBlur(overlay, (21, 21), 0)
        frame[:] = cv2.addWeighted(frame, 1.0, glow, 0.8, 0)
        frame[:] = cv2.add(frame, overlay)

    def draw_blue_attraction(self, frame, cx, cy, physics_system, fw, fh):
        """
        Blue (Anime Quality): Núcleo de energía super denso.
        Líneas de campo magnético atrayendo todo hacia adentro.
        """
        # Spawn partículas ambientales extra para demostrar la fuerza de succión
        physics_system.spawn_ambient(fw, fh, count=20, color=(255, 250, 150)) # Más cian claro

        # Fuerza centrípeta extrema
        physics_system.apply_attraction(cx, cy, strength=8.0)
        physics_system.update(damping=0.90)
        physics_system.render(frame, base_size=3)

        # Dibujar lineas de campo magnético (espirales colapsando)
        t = time.time() * 5
        for spir in range(8):
            pts = []
            for r in range(10, 400, 20):
                # Espiral logarítmica invertida
                ang = r * 0.02 + t + (spir * math.pi / 4)
                x = int(cx + math.cos(ang) * r)
                y = int(cy + math.sin(ang) * r)
                pts.append((x, y))
            
            for i in range(len(pts)-1):
                p1, p2 = pts[i], pts[i+1]
                if 0 <= p1[0] < fw and 0 <= p1[1] < fh:
                    alpha = 1.0 - (i / len(pts))
                    color = (int(255 * alpha), int(255 * alpha), int(100 * alpha))
                    cv2.line(frame, p1, p2, color, max(1, int(3*alpha)))

        # Núcleo 
        pulse = int(25 + 10 * math.sin(time.time() * 15))
        core_glow = np.zeros_like(frame)
        cv2.circle(core_glow, (cx, cy), pulse, (255, 220, 100), -1)
        cv2.circle(core_glow, (cx, cy), pulse + 15, (255, 150, 50), -1)
        
        # Efecto Black-hole Inverso (Centro negro purísimo rodeado de luz intensa)
        glow = cv2.GaussianBlur(core_glow, (41, 41), 0)
        frame[:] = cv2.addWeighted(frame, 1.0, glow, 1.5, 0)
        cv2.circle(frame, (cx, cy), pulse - 5, (0, 0, 0), -1) # Núcleo oscuro super-denso

    def draw_red_repulsion(self, frame, cx, cy, physics_system, fw, fh):
        """
        Red (Reversal): Onda de choque roja que empuja partículas hacia los bordes.
        Invierte la polaridad del campo vectorial.
        """
        # Spawn partículas desde el centro
        for _ in range(5):
            if len(physics_system.particles) < physics_system.max_particles:
                from core.physics import Particle
                p = Particle(
                    x=cx + random.randint(-20, 20),
                    y=cy + random.randint(-20, 20),
                    life=random.randint(40, 100),
                    color=(50, 50, 255)  # Rojo en BGR
                )
                physics_system.particles.append(p)

        # Aplicar fuerza centrífuga (repulsión)
        physics_system.apply_repulsion(cx, cy, strength=4.0)
        physics_system.update(damping=0.96)
        physics_system.render(frame, base_size=3)

        # Ondas de choque expansivas
        t = time.time()
        for wave in range(3):
            r = int((((t * 2 + wave) % 1.0) * 200))
            alpha = max(0, 1.0 - r / 200)
            color = (0, int(50 * alpha), int(255 * alpha))
            cv2.circle(frame, (cx, cy), r, color, 1)

        # Núcleo rojo
        cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)
        cv2.circle(frame, (cx, cy), 14, (0, 80, 255), 2)

    def draw_hollow_purple(self, frame, cx, cy, physics_system, fw, fh):
        """
        Hollow Purple: Fusión de Blue + Red. Esfera morada eléctrica
        con estela de 'borrado de píxeles'.
        """
        # Mantener la estela (últimas N posiciones del centro)
        self._purple_trail.append((cx, cy))
        if len(self._purple_trail) > 30:
            self._purple_trail.pop(0)

        # Dibujar estela de borrado (píxeles negros erosionados)
        for i, (tx, ty) in enumerate(self._purple_trail):
            alpha = i / len(self._purple_trail)
            r = int(20 * (1.0 - alpha))
            if 0 <= tx < fw and 0 <= ty < fh:
                cv2.circle(frame, (tx, ty), r, (10, 0, 10), -1)  # "Borrado"

        # Partículas rojas y azules fusionándose
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(20, 60)
            px = int(cx + math.cos(angle) * r)
            py = int(cy + math.sin(angle) * r)
            if 0 <= px < fw and 0 <= py < fh:
                if random.random() < 0.5:
                    cv2.circle(frame, (px, py), 2, (255, 80, 30), -1)   # Azul
                else:
                    cv2.circle(frame, (px, py), 2, (50, 30, 255), -1)   # Rojo

        # Esfera púrpura central (eléctrica y pulsante)
        pulse = int(18 + 8 * math.sin(time.time() * 10))
        cv2.circle(frame, (cx, cy), pulse, (200, 0, 200), -1)
        cv2.circle(frame, (cx, cy), pulse + 5, (255, 50, 255), 2)
        cv2.circle(frame, (cx, cy), pulse + 12, (220, 100, 255), 1)

        # Chispas eléctricas
        for _ in range(6):
            x1 = cx + random.randint(-pulse, pulse)
            y1 = cy + random.randint(-pulse, pulse)
            x2 = x1 + random.randint(-20, 20)
            y2 = y1 + random.randint(-20, 20)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 150, 255), 1)
