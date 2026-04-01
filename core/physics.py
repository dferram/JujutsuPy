"""
core/physics.py — Motor de Física de Partículas

Implementa un sistema de partículas con fuerzas vectoriales:
- Atracción (Gojo Blue / Lapse): Fuerza centrípeta F = -k * r_hat
- Repulsión (Gojo Red / Reversal): Fuerza centrífuga F = k * r_hat  
- Fusión (Hollow Purple): Superposición de ambos campos + aniquilación

Cada partícula tiene posición (x, y) y velocidad (vx, vy).
Las fuerzas se aplican como aceleraciones sobre los vectores de velocidad.
"""

import numpy as np
import random
import math


class Particle:
    """Partícula individual con posición y velocidad."""
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color']

    def __init__(self, x, y, vx=0.0, vy=0.0, life=120, color=(255, 200, 100)):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color


class PhysicsParticleSystem:
    """
    Sistema de partículas con simulación física basada en vectores.
    
    Implementación del modelo de fuerzas:
    - Para cada partícula P con posición r_p y un centro de fuerza C:
      - Vector dirección: d = C - r_p
      - Distancia: |d| = sqrt(dx^2 + dy^2)
      - Vector unitario: d_hat = d / |d|
      - Fuerza de atracción:  F = strength * d_hat / max(|d|, epsilon)
      - Fuerza de repulsión:  F = -strength * d_hat / max(|d|, epsilon)
    """

    def __init__(self, max_particles=300):
        self.max_particles = max_particles
        self.particles = []
        self._spawn_timer = 0

    def spawn_ambient(self, fw, fh, count=5, color=(100, 80, 60)):
        """Genera partículas de fondo aleatorias (micro-partículas ambientales)."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            p = Particle(
                x=random.uniform(0, fw),
                y=random.uniform(0, fh),
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(-0.5, 0.5),
                life=random.randint(60, 180),
                color=color
            )
            self.particles.append(p)

    def apply_attraction(self, cx, cy, strength=2.0):
        """
        Aplica fuerza centrípeta (Blue de Gojo).
        Todas las partículas son atraídas hacia (cx, cy).
        
        F = strength * d_hat / max(|d|, 5.0)
        """
        for p in self.particles:
            dx = cx - p.x
            dy = cy - p.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 5.0:
                dist = 5.0  # Evita singularidad (división por cero)

            # Normalización del vector + aplicación de fuerza
            force = strength / dist
            p.vx += (dx / dist) * force
            p.vy += (dy / dist) * force

    def apply_repulsion(self, cx, cy, strength=3.0):
        """
        Aplica fuerza centrífuga (Red de Gojo).
        Todas las partículas son repelidas desde (cx, cy).
        
        F = -strength * d_hat / max(|d|, 5.0)
        """
        for p in self.particles:
            dx = p.x - cx
            dy = p.y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 5.0:
                dist = 5.0

            force = strength / dist
            p.vx += (dx / dist) * force
            p.vy += (dy / dist) * force

    def update(self, damping=0.95):
        """
        Paso de simulación: Integración de Euler.
        x(t+1) = x(t) + v(t) * dt   (dt = 1 frame)
        v(t+1) = v(t) * damping      (fricción para estabilidad)
        """
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vx *= damping
            p.vy *= damping
            p.life -= 1

            if p.life > 0:
                alive.append(p)

        self.particles = alive

    def render(self, frame, base_size=2):
        """Renderiza todas las partículas vivas en el frame."""
        import cv2
        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                # Opacidad basada en vida restante
                alpha = p.life / p.max_life
                r = max(1, int(base_size * (0.5 + alpha)))
                cv2.circle(frame, (px, py), r, p.color, -1)

                # Glow ocasional
                if random.random() < 0.1 * alpha:
                    glow_color = tuple(min(255, int(c * 1.5)) for c in p.color)
                    cv2.circle(frame, (px, py), r + 3, glow_color, 1)

    def clear(self):
        """Limpia todas las partículas."""
        self.particles.clear()
