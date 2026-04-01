# JujutsuPy V5.0

Real-time hand gesture recognition system built with MediaPipe and OpenCV. The application detects specific hand configurations (seals) inspired by Jujutsu Kaisen and renders corresponding high-fidelity visual effects.

Developed for FIF Hackathon 2026.

---

## 🚀 Version 5.0 Features

- **Abstract Noise Shaders:** Hollow Purple now uses an iterative CGI noise generator with starry particle fields.
- **Vector Flame Polygons:** Cursed Energy (Ambient) and Nanami's Overtime use trigonometric jagged polygons for a traditional anime feel.
- **Cinematic Screen Shake:** Violent frame-shaking effects upon technique activation for visceral impact.
- **Interactive Tutorials:** Mouse-clickable sidebar that renders 3D holographic wireframe blueprints of hand seals.
- **Military-Grade Tracking:** 0.85 MediaPipe confidence baseline with EMA (Exponential Moving Average) smoothing.

---

## Architecture

```
                  +------------------+
                  |     Webcam       |
                  +--------+---------+
                           |
                           v
                  +------------------+
                  |  MediaPipe Hands |
                  |  (21 Landmarks   |
                  |   per hand)      |
                  +--------+---------+
                           |
                           v
               +------------+-------------+
               |   Gesture Dispatcher     |
               |   (gestures.py)          |
               |                          |
               |  Evaluates 9 geometric   |
               |  signatures with         |
               |  priority ordering       |
               +------------+-------------+
                           |
                    technique_id
                           |
               +------------+-------------+
               |                          |
      +--------v--------+     +----------v----------+
      |  Effect Engine   |     |   Physics Engine    |
      |  (effects.py)    |     |   (physics.py)      |
      |                  |     |                     |
      |  Abstract Noise  |     |  Vector forces:     |
      |  Flame Polygons  |     |  Attraction (Blue)  |
      |  Super-Bloom     |     |  Repulsion (Red)    |
      +--------+---------+     |  Euler integration  |
               |               +----------+----------+
               |                          |
               +------------+-------------+
                           |
                           v
               +------------------------+
               |   Cinematic Renderer   |
               |   (renderer.py)        |
               |                        |
               |   Interactive HUD      |
               |   Clickable Tutorials  |
               |   Screen Shake         |
               +------------------------+
```

---

## Available Techniques

### Satoru Gojo -- Limitless

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Infinite Void   | Middle finger crossed over index         | Cosmic portal with rotating rings                |
| Blue (Lapse)    | Open palm, fingers spread                | High-intensity gravity well                      |
| Red (Reversal)  | Index finger pointing vertically up      | Crimson shockwave with repulsion forces          |
| Hollow Purple   | One-handed shooting pose (Gun)           | **V5 Abstract Noise Orb** + Starry field         |

### Megumi Fushiguro -- Ten Shadows

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Divine Dogs     | Palms together, thumbs up                | Dark-matter wolf silhouette                      |
| Nue             | Crossed wrists, open hands               | Electric 2D wings with glowing cores             |
| Mahoraga        | Both fists stacked vertically            | Eight-spoke golden spinning wheel                |

### Kento Nanami -- Ratio Technique

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Overtime Aura   | Closed fist held for 2 seconds           | **Blue/Yellow Flame Polygons** (Anime Style)     |
| Ratio 7:3       | Knife hand (palm sideways)               | High-intensity laser beam with chromatic aberration |

---

## Setup and Installation

Requirements: Python 3.10 or higher and a working webcam.

```bash
# Clone the repository
git clone https://github.com/dferram/JujutsuPy.git
cd JujutsuPy

# Windows Launcher
run_jujutsu.bat
```

Press `q` in the OpenCV window to close.

---

## Project Structure

```
JujutsuPy/
|-- main.py                  # Entry Point
|-- run_jujutsu.bat          # One-click Launcher
|-- core/
|   |-- vision_engine.py     # Main Render Loop & Screen Shake
|   |-- gestures.py          # Pruned 9-Technique Dispatcher
|   |-- effects.py           # V5 Noise & Flame Shaders
|   |-- physics.py           # Force Engine
|   |-- renderer.py          # Interactive FUI & Tutorials
```
