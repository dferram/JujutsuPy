"""
core/hud.py — Heads-Up Display: Barra de Energía Maldita y UI de estado.

Renderiza la barra de energía, el nombre del personaje activo, y la técnica actual.
"""

import cv2
import time


# Colores por personaje (BGR)
CHARACTER_COLORS = {
    "Megumi":   (128, 0, 128),    # Morado
    "Nanami":   (0, 200, 255),    # Amarillo/dorado
    "Higuruma": (0, 215, 255),    # Dorado
    "Yuta":     (200, 200, 220),  # Blanco fantasmal
    "default":  (180, 50, 180),   # Morado genérico
}


class CursedEnergySystem:
    """
    Sistema de Energía Maldita.
    Se gasta al mantener activa una técnica y se regenera de forma pasiva.
    """
    def __init__(self, max_energy=100.0):
        self.max_energy = max_energy
        self.current_energy = max_energy
        self.drain_rate = 8.0      # Unidades por segundo que se gastan
        self.regen_rate = 5.0      # Unidades por segundo que se regeneran
        self.last_update = time.time()

    def update(self, is_active):
        """Actualiza la energía basado en si hay una técnica activa o no."""
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        if is_active:
            self.current_energy = max(0, self.current_energy - self.drain_rate * dt)
        else:
            self.current_energy = min(self.max_energy, self.current_energy + self.regen_rate * dt)

    def has_energy(self):
        return self.current_energy > 2.0

    def get_ratio(self):
        return self.current_energy / self.max_energy


def draw_hud(frame, energy_system, technique_name=None, character=None):
    """
    Renderiza el HUD completo en el frame:
    - Barra de energía maldita (esquina inferior izquierda)
    - Nombre de la técnica activa (parte superior)
    - Nombre del personaje
    """
    fh, fw = frame.shape[:2]
    char_color = CHARACTER_COLORS.get(character, CHARACTER_COLORS["default"])

    # --- Barra de Energía Maldita ---
    bar_x, bar_y = 20, fh - 50
    bar_w, bar_h = 250, 20
    ratio = energy_system.get_ratio()

    # Fondo de la barra
    cv2.rectangle(frame, (bar_x - 2, bar_y - 2),
                  (bar_x + bar_w + 2, bar_y + bar_h + 2), (60, 60, 60), -1)

    # Barra de energía (color basado en nivel)
    if ratio > 0.5:
        bar_color = (180, 50, 180)  # Morado (bien)
    elif ratio > 0.2:
        bar_color = (0, 150, 255)   # Naranja (precaución)
    else:
        bar_color = (0, 0, 200)     # Rojo (peligro)

    fill_w = int(bar_w * ratio)
    if fill_w > 0:
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + fill_w, bar_y + bar_h), bar_color, -1)

    # Borde
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 1)

    # Etiqueta
    cv2.putText(frame, f"Cursed Energy: {int(energy_system.current_energy)}%",
                (bar_x, bar_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # --- Técnica Activa ---
    if technique_name and character:
        # Personaje
        cv2.putText(frame, f"[{character.upper()}]", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, char_color, 2)
        # Técnica
        cv2.putText(frame, technique_name, (30, 70),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, char_color, 2)
    else:
        cv2.putText(frame, "Esperando sello...", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
