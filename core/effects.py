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

    def _draw_fluid_silhouette(self, frame, points, base_cx, base_cy, scale, color=(128, 0, 128), glow_color=(200, 50, 200)):
        """Método V4 NumPy fluido para renderizar siluetas con miles de micro-partículas orgánicas."""
        num_per_edge = 90
        t_vals = np.linspace(0, 1, num_per_edge)
        
        all_x = []
        all_y = []
        t = time.time()
        
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            
            x_edge = p1[0] + (p2[0] - p1[0]) * t_vals
            y_edge = p1[1] + (p2[1] - p1[1]) * t_vals
            
            # Fluid Math (Seno + Ruido Gaussiano)
            noise_x = np.random.normal(0, 8, num_per_edge) + np.sin(t_vals * 15 + t*5) * 12
            noise_y = np.random.normal(0, 8, num_per_edge) + np.cos(t_vals * 15 + t*5) * 12
            
            all_x.extend(base_cx + x_edge * scale + noise_x)
            all_y.extend(base_cy + y_edge * scale + noise_y)
            
        overlay = np.zeros_like(frame)
        for px, py in zip(all_x, all_y):
            if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                # Pequeños cubos y cuadrados
                cv2.rectangle(overlay, (int(px), int(py)), (int(px)+2, int(py)+2), color, -1, cv2.LINE_AA)
                
        # Super capa de Glow Cinematográfico Aditivo
        glow = cv2.GaussianBlur(overlay, (31, 31), 0)
        cv2.addWeighted(frame, 1.0, glow, 2.5, 0, frame)
        cv2.add(frame, overlay, frame)

    # =========================================================================
    #  MEGUMI FUSHIGURO
    # =========================================================================

    def draw_divine_dogs(self, frame, cx, cy, scale=130):
        """Masa fluida de micro-partículas negras/moradas congregándose en lobos."""
        # Perro Izquierdo y Derecho
        self._draw_fluid_silhouette(frame, self._wolf_points, cx - 200, cy, scale, color=(50, 20, 80))
        self._draw_fluid_silhouette(frame, self._wolf_points, cx + 200, cy, scale, color=(200, 200, 220))

    def draw_nue(self, frame, cx, cy, scale=140):
        """Alas formadas por chispas eléctricas masivas y fluido de partículas."""
        self._draw_fluid_silhouette(frame, self._nue_points, cx, cy, scale, color=(230, 230, 50))

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
        """Lenguas de fluido verde orgánico lanzándose hacia los bordes."""
        t = time.time()
        targets = [(0, cy), (fw, cy), (cx, 0), (cx, fh)]
        overlay = np.zeros_like(frame)
        
        for tx, ty in targets:
            num_dots = 120
            t_vals = np.linspace(0, 1, num_dots)
            
            # Lenguas oscilando con el tiempo
            reach = 0.5 + 0.3 * np.sin(t * 10)
            valid_t = t_vals[t_vals < reach]
            
            x_vals = cx + (tx - cx) * valid_t
            y_vals = cy + (ty - cy) * valid_t
            
            # Bamboleo del fluido
            noise_x = np.sin(valid_t * 20 + t * 15) * 15
            noise_y = np.cos(valid_t * 20 + t * 15) * 15
            
            for px, py in zip(x_vals + noise_x, y_vals + noise_y):
                if 0 <= px < fw and 0 <= py < fh:
                    cv2.rectangle(overlay, (int(px), int(py)), (int(px)+3, int(py)+3), (30, 200, 80), -1, cv2.LINE_AA)
                    
        glow = cv2.GaussianBlur(overlay, (21, 21), 0)
        cv2.addWeighted(frame, 1.0, glow, 2.0, 0, frame)
        cv2.add(frame, overlay, frame)

    def draw_max_elephant(self, frame, cx, cy, fw):
        """Cascada masiva de fluido azul/blanco cayendo desde el cielo usando matrices."""
        overlay = np.zeros_like(frame)
        num_drops = 600
        
        # Torrente cayendo
        x_vals = np.random.normal(cx, 150, num_drops)
        y_vals = np.random.uniform(0, cy, num_drops)
        
        for px, py in zip(x_vals, y_vals):
            if 0 <= px < fw and 0 <= py < frame.shape[0]:
                size = random.randint(2, 6)
                cv2.rectangle(overlay, (int(px), int(py)), (int(px)+size, int(py)+size), (250, 200, 50), -1, cv2.LINE_AA)
                
        glow = cv2.GaussianBlur(overlay, (21, 21), 0)
        cv2.addWeighted(frame, 1.0, glow, 1.5, 0, frame)
        cv2.add(frame, overlay, frame)

    def draw_rabbit_escape(self, frame, fw, fh):
        """Enjambre masivo de miles de partículas blancas parpadeantes (Enjambre)."""
        overlay = np.zeros_like(frame)
        num = len(self._rabbit_particles)
        
        # Swarming vectorizado
        rx, ry = zip(*self._rabbit_particles)
        rx = np.array(rx) + np.random.uniform(-0.025, 0.025, num)
        ry = np.array(ry) + np.random.uniform(-0.025, 0.025, num)
        
        # Envuelve la pantalla
        rx = rx % 1.0
        ry = ry % 1.0
        self._rabbit_particles = list(zip(rx, ry))
        
        px_vals = (rx * fw).astype(int)
        py_vals = (ry * fh).astype(int)
        
        glow_mask = np.random.random(num) < 0.1
        
        for px, py, is_glow in zip(px_vals, py_vals, glow_mask):
            cv2.rectangle(overlay, (px, py), (px+3, py+3), (250, 250, 250), -1, cv2.LINE_AA)
            if is_glow:
                cv2.circle(overlay, (px, py), 8, (255, 255, 255), 1, cv2.LINE_AA)
                
        glow = cv2.GaussianBlur(overlay, (15, 15), 0)
        cv2.addWeighted(frame, 1.0, glow, 2.0, 0, frame)
        cv2.add(frame, overlay, frame)

    def draw_mahoraga_wheel(self, frame, cx, cy, scale=220):
        """Rueda de miles de partículas doradas vibrando."""
        self._wheel_angle += 0.03
        overlay = np.zeros_like(frame)
        t = time.time()
        
        # 3000 Micro-partículas doradas
        num_particles = 3000
        angles = np.random.uniform(0, 2 * math.pi, num_particles)
        radii = np.zeros(num_particles)
        
        is_spoke = np.random.random(num_particles) > 0.25
        
        # 75% en los Radios, 25% en el Aro
        for i in range(num_particles):
            if is_spoke[i]:
                radii[i] = np.random.uniform(0, scale)
                closest_spoke = round((angles[i] - self._wheel_angle) / (math.pi / 4))
                angles[i] = closest_spoke * (math.pi / 4) + self._wheel_angle + np.random.normal(0, 0.015)
            else:
                radii[i] = scale + np.random.normal(0, 5)
                
        # Termo-vibración fluida matemática (Funciones de onda complejas)
        vibration_r = np.sin(t * 15 + angles * 8) * 6
        radii += vibration_r
        
        x_vals = cx + np.cos(angles) * radii
        y_vals = cy + np.sin(angles) * radii
        
        for px, py in zip(x_vals, y_vals):
            if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                cv2.rectangle(overlay, (int(px), int(py)), (int(px)+2, int(py)+2), (0, 215, 255), -1, cv2.LINE_AA)
                
        glow = cv2.GaussianBlur(overlay, (41, 41), 0)
        cv2.addWeighted(frame, 1.0, glow, 2.5, 0, frame)
        cv2.add(frame, overlay, frame)

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

    def draw_ratio_line(self, frame, cx, cy, length=800):
        """
        Nanami 7:3 Ratio (Anime Quality): Haz de luz láser gigante con 
        aberración cromática y destellos masivos.
        """
        x_start = cx - length // 2
        x_end = cx + length // 2
        crit_x = int(x_start + length * 0.7)
        
        # Buffer negro para el láser y composicion
        laser_overlay = np.zeros_like(frame)
        
        # Aberración cromática (RGB offset brutal)
        offsets = [
            (-8, 0, (0, 0, 255)),  # Rojo puro (Cian ausente)
            (0, 0, (0, 255, 0)),   # Verde
            (8, 0, (255, 0, 0))    # Azul
        ]
        
        for ox, oy, color in offsets:
            cv2.line(laser_overlay, (x_start + ox, cy + oy), (x_end + ox, cy + oy), color, 6, cv2.LINE_AA)
            cv2.circle(laser_overlay, (crit_x + ox, cy + oy), 18, color, -1, cv2.LINE_AA)

        # Blur masivo para crear el volumen lumínico
        glow = cv2.GaussianBlur(laser_overlay, (31, 31), 0)
        
        # Núcleo blanco caliente incandescente
        cv2.line(laser_overlay, (x_start, cy), (x_end, cy), (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(laser_overlay, (crit_x, cy), 10, (255, 255, 255), -1, cv2.LINE_AA)
        
        # Composicion Additive Blending
        frame[:] = cv2.addWeighted(frame, 1.0, glow, 2.0, 0)
        frame[:] = cv2.add(frame, laser_overlay)
        
        # Interfaz Analítica del ratio
        cv2.putText(frame, "7:3 CRITICAL TARGET LOCKED", (crit_x - 120, cy - 40),
                    cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Rayos perpendiculares en la cruz del 7:3
        t = time.time()
        c_pulse = int(50 + 20 * math.sin(t*15))
        cv2.line(frame, (crit_x, cy - c_pulse), (crit_x, cy + c_pulse), (200, 200, 255), 2, cv2.LINE_AA)

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
        Blue (Anime Quality): Vórtice de Flow Field y densidad variable.
        Las partículas forman colas de cometa marcando las trayectorias curvas.
        """
        physics_system.spawn_ambient(fw, fh, count=25, color=(255, 250, 150))

        physics_system.apply_attraction(cx, cy, strength=9.0)
        physics_system.update(damping=0.88)
        
        # Buffer para las trayectorias de absorción (flow field)
        overlay = np.zeros_like(frame)
        
        for p in physics_system.particles:
            px, py = int(p.x), int(p.y)
            # Cola de velocidad (multiplicada inversamente al damping)
            tail_x = int(p.x - p.vx * 3.5)
            tail_y = int(p.y - p.vy * 3.5)
            if 0 <= px < fw and 0 <= py < fh and 0 <= tail_x < fw and 0 <= tail_y < fh:
                # Estelas finas anti-aliased
                cv2.line(overlay, (tail_x, tail_y), (px, py), p.color, max(1, p.size), cv2.LINE_AA)

        # Núcleo de Densidad Oscura rodeada de luz
        pulse = int(35 + 10 * math.sin(time.time() * 15))
        core_glow = np.zeros_like(frame)
        cv2.circle(core_glow, (cx, cy), pulse, (255, 220, 100), -1, cv2.LINE_AA)
        cv2.circle(core_glow, (cx, cy), pulse + 30, (255, 120, 0), -1, cv2.LINE_AA)
        
        glow = cv2.GaussianBlur(core_glow, (61, 61), 0)
        frame[:] = cv2.addWeighted(frame, 1.0, glow, 2.5, 0)
        frame[:] = cv2.add(frame, overlay)
        cv2.circle(frame, (cx, cy), pulse - 10, (10, 5, 10), -1, cv2.LINE_AA) 

    def draw_red_repulsion(self, frame, cx, cy, physics_system, fw, fh):
        """
        Red (Anime Quality): Onda de choque expansiva de energía carmesí.
        Campo de flujo inverso masivo.
        """
        # Spawns explosivos en el centro
        for _ in range(10):
            if len(physics_system.particles) < physics_system.max_particles:
                from core.physics import Particle
                p = Particle(
                    x=cx + random.randint(-10, 10),
                    y=cy + random.randint(-10, 10),
                    life=random.randint(40, 100),
                    color=(50, 50, 255)  # Rojo BGR
                )
                physics_system.particles.append(p)

        physics_system.apply_repulsion(cx, cy, strength=12.0)
        physics_system.update(damping=0.98) # Muy poca fricción para que salgan volando
        
        overlay = np.zeros_like(frame)
        
        # Rayos de explosión de plasma
        for p in physics_system.particles:
            px, py = int(p.x), int(p.y)
            tail_x = int(p.x - p.vx * 5)
            tail_y = int(p.y - p.vy * 5)
            if 0 <= px < fw and 0 <= py < fh and 0 <= tail_x < fw and 0 <= tail_y < fh:
                cv2.line(overlay, (tail_x, tail_y), (px, py), p.color, max(1, p.size + 1), cv2.LINE_AA)

        # Capa estruendosa roja
        core_glow = np.zeros_like(frame)
        cv2.circle(core_glow, (cx, cy), 50, (30, 30, 255), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(core_glow, (81, 81), 0)
        
        # Anillos destructivos
        t = time.time()
        for ring in range(3):
            r = int(((t * 4 + ring) % 1.0) * 800)
            alfa = max(0, 1.0 - r / 800)
            color = (0, int(30 * alfa), int(255 * alfa))
            cv2.circle(overlay, (cx, cy), r, color, int(2+6*alfa), cv2.LINE_AA)
            
        frame[:] = cv2.addWeighted(frame, 1.0, glow, 3.0, 0)
        frame[:] = cv2.add(frame, overlay)
        cv2.circle(frame, (cx, cy), 20, (200, 200, 255), -1, cv2.LINE_AA)

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
