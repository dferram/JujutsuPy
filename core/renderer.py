"""
core/renderer.py — Motor de Renderizado Cinematografico

Este modulo toma el control de toda la capa visual.
Dibuja un canvas 1080p, un entorno cosmico, una interfaz limpia, 
e inyecta la webcam original con esquinas redondeadas y neones de landmarks.
"""

import cv2
import cvzone
import numpy as np
import math
import random
import time
from PIL import Image, ImageDraw, ImageFont


class CinematicRenderer:
    def __init__(self, width=1920, height=1080):
        self.W = width
        self.H = height
        self.bg_particles = self._init_cosmic_background(800)

        # Inset config
        self.inset_w = 480
        self.inset_h = 270
        self.inset_x = 40
        self.inset_y = self.H - self.inset_h - 40

        # Cargar fuente japonesa para poder dibujar "呪術廻戦" nativamente
        self.jp_font = None
        self.tech_font = None
        
        # Test common Windows fonts
        font_paths = [
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/meiryo.ttc"
        ]
        for path in font_paths:
            try:
                self.jp_font = ImageFont.truetype(path, 70)
                self.tech_font = ImageFont.truetype(path, 30)
                break
            except Exception:
                continue

    def _init_cosmic_background(self, count):
        """Genera distribucion gaussiana de particulas cosmicas y datos."""
        particles = []
        for _ in range(count):
            # Campana de Gauss para concentrar hacia el centro
            x = int(random.gauss(self.W / 2, self.W / 3))
            y = int(random.gauss(self.H / 2, self.H / 3))
            
            x = max(0, min(self.W - 1, x))
            y = max(0, min(self.H - 1, y))

            vx = random.uniform(-0.2, 0.2)
            vy = random.uniform(-0.2, 0.2)
            size = random.choice([1, 1, 2, 2, 3])
            
            # Paleta cyberpunk/mística BGR
            color = random.choice([
                (255, 255, 255),  # Blanco
                (255, 255, 100),  # Cian claro
                (200, 100, 50),   # Azul mediano
                (80, 20, 10),     # Azul profundo oscuro
                (200, 200, 200)   # Gris brillante
            ])
            shape = random.choice(['circle', 'square'])
            particles.append([x, y, vx, vy, size, color, shape])
        return particles

    def create_canvas(self):
        """Retorna el buffer principal donde dibujaremos todo."""
        return np.zeros((self.H, self.W, 3), dtype=np.uint8)

    def draw_background(self, canvas):
        """Actualiza y dibuja las particulas del fondo cosmico con antialiasing."""
        for p in self.bg_particles:
            p[0] += p[2]  # Update X
            p[1] += p[3]  # Update Y
            
            # Wrap around
            if p[0] < 0: p[0] = self.W
            if p[0] >= self.W: p[0] = 0
            if p[1] < 0: p[1] = self.H
            if p[1] >= self.H: p[1] = 0

            px, py = int(p[0]), int(p[1])
            s = p[4]
            c = p[5]
            
            if p[6] == 'circle':
                cv2.circle(canvas, (px, py), s, c, -1, cv2.LINE_AA)
            else:
                cv2.rectangle(canvas, (px, py), (px + s, py + s), c, -1, cv2.LINE_AA)

    def draw_glass_panel(self, canvas, x, y, w, h, alpha=0.25, color=(15, 10, 25), border_color=(80, 220, 255)):
        """Dibuja un panel translucido estilo Vidrio Esmerilado (Frosted Glass / MAPPA UI)."""
        # Evitar recortes fuera de limites
        if y+h > self.H or x+w > self.W or x < 0 or y < 0: return

        overlay = canvas[y:y+h, x:x+w].copy()
        cv2.rectangle(overlay, (0, 0), (w, h), color, -1)
        
        # Desenfoque masivo para el efecto "Frosted"
        overlay = cv2.GaussianBlur(overlay, (45, 45), 0)
        cv2.addWeighted(overlay, alpha, canvas[y:y+h, x:x+w], 1 - alpha, 0, canvas[y:y+h, x:x+w])
        
        # Borde exterior fino e iluminado
        cv2.rectangle(canvas, (x, y), (x + w, y + h), border_color, 1, cv2.LINE_AA)
        
        # Acentos geometricos en esquinas (estilo militar/sci-fi)
        leng = 15
        thk = 2
        # Arriba-Izq
        cv2.line(canvas, (x, y), (x + leng, y), border_color, thk, cv2.LINE_AA)
        cv2.line(canvas, (x, y), (x, y + leng), border_color, thk, cv2.LINE_AA)
        # Abajo-Der
        cv2.line(canvas, (x + w, y + h), (x + w - leng, y + h), border_color, thk, cv2.LINE_AA)
        cv2.line(canvas, (x + w, y + h), (x + w, y + h - leng), border_color, thk, cv2.LINE_AA)

    def draw_webcam_inset(self, canvas, cam_frame, landmarks_list):
        """
        Dibuja el inset limpisimo del usuario abajo a la izquierda, 
        y dibuja los neones limpios de las manos SOLO encima del inset.
        """
        # Dibujar landmarks sobre el cam_frame puro (sin tocar el canvas yet)
        h_cam, w_cam = cam_frame.shape[:2]
        
        # Filtro muy leve para hacer lucir tech
        cam_frame = cv2.addWeighted(cam_frame, 0.9, np.zeros_like(cam_frame), 0.1, 0)
        
        for wrapper in landmarks_list:
            self._draw_neon_hand(cam_frame, wrapper.landmark, w_cam, h_cam)

        # Resize al tamaño del inset
        inset_bgr = cv2.resize(cam_frame, (self.inset_w, self.inset_h), interpolation=cv2.INTER_AREA)

        # Borde sci-fi con cvzone
        # Colocamos el inset en el canvas
        canvas[self.inset_y : self.inset_y + self.inset_h, self.inset_x : self.inset_x + self.inset_w] = inset_bgr
        
        # Dibujar un borde futurista y escaner dinamico
        cvzone.putTextRect(canvas, 'LIVE SENSOR HUB', (self.inset_x, self.inset_y - 12), 
                           scale=1.2, thickness=1, colorT=(255, 255, 255), colorR=(15, 10, 25), 
                           font=cv2.FONT_HERSHEY_PLAIN, offset=5)
        
        cv2.rectangle(canvas, (self.inset_x, self.inset_y), 
                      (self.inset_x + self.inset_w, self.inset_y + self.inset_h), 
                      (255, 255, 100), 1, cv2.LINE_AA)

        # Animacion de Escaner Laser
        t = time.time()
        scan_y = int(((math.sin(t * 3) + 1) / 2) * self.inset_h)
        scan_line_y = self.inset_y + scan_y
        cv2.line(canvas, (self.inset_x, scan_line_y), (self.inset_x + self.inset_w, scan_line_y), (100, 255, 200), 1, cv2.LINE_AA)
        # Glow del escaner
        cv2.circle(canvas, (self.inset_x, scan_line_y), 3, (200, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, (self.inset_x + self.inset_w, scan_line_y), 3, (200, 255, 255), -1, cv2.LINE_AA)

    def _draw_neon_hand(self, img, landmarks, w, h):
        """Lineas neon puras ultra-finas sin alias."""
        points = {}
        for idx, lm in enumerate(landmarks):
            px, py = int(lm.x * w), int(lm.y * h)
            points[idx] = (px, py)
            cv2.circle(img, (px, py), 2, (255, 255, 255), -1, cv2.LINE_AA) 
            cv2.circle(img, (px, py), 5, (255, 255, 50), 1, cv2.LINE_AA) 

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 17), (5, 9), (9, 13), (13, 17),
            (9, 10), (10, 11), (11, 12),
            (13, 14), (14, 15), (15, 16),
            (17, 18), (18, 19), (19, 20),
        ]
        
        for c1, c2 in connections:
            if c1 in points and c2 in points:
                cv2.line(img, points[c1], points[c2], (255, 200, 50), 1, cv2.LINE_AA)
                
    def draw_professional_hud(self, canvas, energy_system, fps, tech_name=None, character=None, is_active=False):
        """Dibuja todo el overlay futurista sobre el canvas 1080p."""

        # --- 0. Panel Compendio Lateral (Glass Morphism) ---
        panel_w, panel_h = 360, 710
        px, py = 40, 45  # Subido para evitar superposición con cámara
        self.draw_glass_panel(canvas, px, py, panel_w, panel_h, alpha=0.35)
        
        cv2.putText(canvas, "SORCERER DB // REGISTERED SEALS", (px + 20, py + 30), cv2.FONT_HERSHEY_PLAIN, 1.1, (200, 220, 255), 1, cv2.LINE_AA)
        cv2.line(canvas, (px + 20, py + 40), (px + panel_w - 20, py + 40), (100, 150, 255), 1, cv2.LINE_AA)

        # Database index mapping (con instrucciones de sellos)
        y_offset = py + 75
        db_entries = [
            ("SATORU GOJO", [
                "Infinite Void (Fingers Crossed)", 
                "Blue (Index/Middle Point)", 
                "Red (Index Point Up)", 
                "Hollow Purple (Shooting Pose)"
            ], (255, 200, 100)),
            ("MEGUMI FUSHIGURO", [
                "Divine Dogs (Palms Joined & Thumbs Up)", 
                "Nue (Crossed Wrists)",
                "Toad (Double Fists)",
                "Mahoraga (Fists Stacked)", 
                "Domain (Middle Fingers Cross)"
            ], (255, 100, 255)),
            ("KENTO NANAMI", [
                "Overtime Aura (Fist Hold 2s)", 
                "Ratio 7:3 (Knife Hand Strike)"
            ], (50, 200, 255)),
            ("HIROMI HIGURUMA", [
                "Deadly Sentencing (Gavel Hit)"
            ], (50, 230, 255)),
            ("YUTA OKKOTSU", [
                "Rika Manifest (Ring Finger Kiss)", 
                "Mutual Love Domain (Heart Sign)"
            ], (230, 230, 250))
        ]

        for sorcerer, skills, col in db_entries:
            # Header del hechicero
            cv2.putText(canvas, f"[{sorcerer}]", (px + 15, y_offset), cv2.FONT_HERSHEY_PLAIN, 1.2, col, 1, cv2.LINE_AA)
            y_offset += 26
            for sk in skills:
                # Iconito tracker
                cv2.circle(canvas, (px + 25, y_offset - 4), 2, col, -1, cv2.LINE_AA)
                cv2.putText(canvas, sk, (px + 35, y_offset), cv2.FONT_HERSHEY_PLAIN, 1.0, (220, 220, 220), 1, cv2.LINE_AA)
                y_offset += 22
            y_offset += 15

        # --- 1. Top Logo (Kanji) ---
        title = "呪術廻戦"
        sub = "JUJUTSU KAISEN VISION ENGINE V3.0"
        
        if self.jp_font:
            try:
                canvas_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(canvas_pil)
                draw.text((self.W//2 - 148, 42), title, font=self.jp_font, fill=(0, 0, 0))
                draw.text((self.W//2 - 150, 40), title, font=self.jp_font, fill=(255, 255, 255))
                canvas[:] = cv2.cvtColor(np.array(canvas_pil), cv2.COLOR_RGB2BGR)
            except Exception:
                pass
        
        cv2.putText(canvas, sub, (self.W//2 - 190, 130), cv2.FONT_HERSHEY_PLAIN, 1.3, (200, 220, 255), 1, cv2.LINE_AA)
        cv2.line(canvas, (self.W//2 - 200, 140), (self.W//2 + 200, 140), (255, 255, 255), 1, cv2.LINE_AA)
        
        # --- 2. Tech Data Overlays & Confirmations ---
        cvzone.putTextRect(canvas, f'FPS {int(fps)} // 1080P', (self.W - 200, 40), 
                           scale=1.2, thickness=1, colorT=(0, 250, 150), colorR=(15, 10, 25), font=cv2.FONT_HERSHEY_PLAIN)
                           
        state_color = (100, 255, 100) if tech_name else (200, 200, 200)
        state_text = 'TARGET ACQUIRED: GESTURE LOCKED' if tech_name else 'AWAITING HAND SIGNATURE...'
        
        # Pulsing text en el HUD derecho
        t = time.time()
        pulse_alpha = abs(math.sin(t * 5)) if tech_name else 1.0
        final_color = (int(state_color[0]*pulse_alpha), int(state_color[1]*pulse_alpha), int(state_color[2]*pulse_alpha))
        
        cvzone.putTextRect(canvas, state_text, (self.W - 420, self.H - 50), 
                           scale=1.2, thickness=1, colorT=final_color, colorR=(15, 10, 25), font=cv2.FONT_HERSHEY_PLAIN)
                           
        # --- 3. Technique Name ---
        if tech_name and is_active:
            # Texto azul celeste gigante tipo anime
            t_size = cv2.getTextSize(tech_name, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)[0]
            tx = self.W // 2 - t_size[0] // 2
            ty = 200
            
            # Glow
            cv2.putText(canvas, tech_name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 200, 50), 8)
            cv2.putText(canvas, tech_name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
