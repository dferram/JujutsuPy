# JujutsuPy

Real-time hand gesture recognition system built with MediaPipe and OpenCV. The application detects specific hand configurations (seals) inspired by Jujutsu Kaisen and renders corresponding particle-based visual effects over the camera feed.

Developed for FIF Hackathon 2026.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Available Techniques](#available-techniques)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Extending the System](#extending-the-system)

---

## Overview

JujutsuPy is a computer vision application that transforms a standard webcam into an interactive gesture recognition engine. Users perform hand seals in front of the camera; the system identifies the geometric signature of each gesture and overlays a corresponding visual effect in real time.

The project implements 16 distinct techniques across 5 fictional characters, each with unique detection logic and rendering behavior. It also includes a vector-based particle physics engine for force-driven visual effects (attraction, repulsion, and field fusion).

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
              |  Evaluates 16 geometric  |
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
     |  Particle interp.|     |  Vector forces:     |
     |  Silhouettes     |     |  Attraction (Blue)  |
     |  Jitter systems  |     |  Repulsion (Red)    |
     +--------+---------+     |  Euler integration  |
              |               +----------+----------+
              |                          |
              +------------+-------------+
                           |
                           v
              +------------------------+
              |   HUD Renderer         |
              |   (hud.py)             |
              |                        |
              |   Cursed Energy bar    |
              |   Technique label      |
              |   FPS counter          |
              +------------------------+
                           |
                           v
              +------------------------+
              |   OpenCV Output        |
              |   cv2.imshow()         |
              +------------------------+
```

### Processing Pipeline

Each frame follows this sequence:

1. **Capture** -- OpenCV reads a BGR frame from the webcam and mirrors it horizontally.
2. **Inference** -- The frame is converted to RGB and passed through the MediaPipe Hands model, which returns up to 2 sets of 21 normalized landmarks.
3. **Detection** -- The gesture dispatcher evaluates all 16 technique signatures against the detected landmarks, using Euclidean distance and finger extension analysis.
4. **Charge Gate** -- A detected gesture must persist for 8 consecutive frames before the technique activates. This prevents false positives.
5. **Rendering** -- The matched technique triggers its corresponding effect renderer, which draws directly onto the frame buffer.
6. **HUD** -- The energy bar, character label, technique name, and FPS counter are composited on top.
7. **Display** -- The final frame is presented via `cv2.imshow`.

---

## Tech Stack

| Component            | Technology         | Purpose                                           |
|----------------------|--------------------|---------------------------------------------------|
| Hand Tracking        | MediaPipe Hands    | Extracts 21 3D landmarks per hand in real time    |
| Frame Processing     | OpenCV 4.x         | Camera I/O, color conversion, drawing primitives  |
| Numerical Operations | NumPy              | Fast array interpolation for particle systems     |
| Language             | Python 3.10+       | Core application logic                            |

No external image assets are used. All visual effects are generated procedurally at runtime through mathematical functions and coordinate interpolation.

---

## How It Works

### Gesture Detection via Analytical Geometry

MediaPipe provides 21 landmark points per hand, each with normalized coordinates in the range [0.0, 1.0]. The system uses these coordinates to compute geometric relationships between key points.

**Euclidean Distance**

The primary metric for evaluating spatial proximity between two landmarks P1(x1, y1) and P2(x2, y2):

```
d(P1, P2) = sqrt((x2 - x1)^2 + (y2 - y1)^2)
```

For example, Divine Dogs is detected when:
- Distance between both wrists (landmark 0) is less than 0.3
- Distance between both index fingertips (landmark 8) is less than 0.15

**Finger Extension Analysis**

A finger is classified as extended when its tip landmark has a lower Y coordinate (higher on screen) than its PIP joint. The thumb uses lateral X-distance from the wrist instead, since it extends sideways rather than vertically.

```
finger_extended = tip.y < pip.y        (for index, middle, ring, pinky)
thumb_extended  = |tip.x - wrist.x| > |ip.x - wrist.x|
```

### Particle Physics Engine

Gojo's techniques (Blue, Red, Hollow Purple) use a force-based simulation. Each particle has position (x, y) and velocity (vx, vy). Forces are applied per frame:

**Attraction (Blue)** -- Centrípetal force pulls particles toward a center point:
```
direction = center - particle_position
force = strength * normalize(direction) / max(|direction|, epsilon)
```

**Repulsion (Red)** -- Centrifugal force pushes particles outward:
```
direction = particle_position - center
force = strength * normalize(direction) / max(|direction|, epsilon)
```

Position updates use Euler integration with damping to prevent divergence:
```
velocity = velocity * damping
position = position + velocity
```

### Cursed Energy System

A resource bar tracks energy consumption. Techniques drain energy at 8 units/second while active, and passive regeneration occurs at 5 units/second when idle. When energy reaches zero, techniques cannot activate.

---

## Available Techniques

### Satoru Gojo -- Limitless

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Infinite Void   | Middle finger crossed over index         | Cosmic portal with rotating concentric rings     |
| Blue (Lapse)    | Open palm, all fingers extended and spread | Gravity well that attracts ambient particles    |
| Red (Reversal)  | Only index finger pointing forward       | Expanding shockwave that repels particles        |
| Hollow Purple   | Both hands in shooting pose, palms together | Purple sphere with pixel-erasure trail          |

### Megumi Fushiguro -- Ten Shadows

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Divine Dogs     | Palms together laterally, thumbs up      | Wolf silhouette in purple particles              |
| Nue             | Crossed wrists, open hands (wings)       | Electric wing particles with lightning bolts      |
| Great Serpent   | Fingers together, thumb tucked (one hand)| Sinusoidal particle trail rising from below       |
| Toad            | Interlaced fingers, index+middle out     | Green tongue particles extending to edges         |
| Max Elephant    | Back-to-back palms, thumbs pointing down | Blue water cascade particles falling              |
| Rabbit Escape   | Peace signs held near head               | Hundreds of white dots moving chaotically         |
| Mahoraga        | All fingertips touching in a circle      | Eight-spoke golden wheel rotating behind user     |

### Kento Nanami -- Ratio Technique

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Overtime        | Closed fist held for 2 seconds           | Dense yellow aura around fist, digital clock     |
| Ratio 7:3       | Knife hand (palm sideways, fingers together) | Blue line with pulsing marker at the 70% point |

### Hiromi Higuruma -- Deadly Sentencing

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Gavel Strike    | Fist colliding with open palm            | Screen darkens, golden balance scales appear     |

### Yuta Okkotsu -- Pure Love

| Technique       | Gesture                                  | Visual Effect                                    |
|-----------------|------------------------------------------|--------------------------------------------------|
| Rika            | Thumb and index touching near face       | Massive black and white particle mass            |
| Domain          | Interlaced hands with crossed indices up | Falling light-point swords with Rika backdrop    |

---

## Project Structure

```
JujutsuPy/
|
|-- main.py                  # Application entry point
|-- requirements.txt         # Pinned dependencies
|-- run_jujutsu.bat          # One-click Windows launcher
|-- .gitignore
|
|-- core/
|   |-- __init__.py
|   |-- vision_engine.py     # Main loop: capture, detection, rendering
|   |-- gestures.py          # 16 gesture validators + priority dispatcher
|   |-- effects.py           # Particle effect renderers (one per technique)
|   |-- physics.py           # Force-based particle simulation engine
|   |-- hud.py               # Energy bar, labels, and overlay UI
|
|-- utils/
    |-- __init__.py
    |-- math_helpers.py       # Euclidean distance, finger state, centroid
```

---

## Setup and Installation

Requirements: Python 3.10 or higher and a working webcam.

```bash
# Clone the repository
git clone https://github.com/dferram/JujutsuPy.git
cd JujutsuPy

# Create a virtual environment
python -m venv venv

# Activate it
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

Alternatively, on Windows you can double-click `run_jujutsu.bat`. It will create the virtual environment, install dependencies, and launch the application automatically.

---

## Usage

```bash
python main.py
```

The application opens a window showing your webcam feed. Perform any of the documented gestures with your hands visible to the camera. A detected gesture must be held for roughly 8 frames before the corresponding effect activates.

Press `q` in the OpenCV window to close the application.

### Controls

| Key | Action             |
|-----|--------------------|
| `q` | Exit the application |

### Tips for Better Detection

- Ensure your hands are well-lit and clearly visible against the background.
- Keep your hands within the camera frame at all times during gesture execution.
- For two-hand gestures, keep both wrists relatively close together.
- Avoid very fast hand movements; the model tracks better with steady poses.

---

## Extending the System

The codebase is designed around a modular pipeline. Adding a new technique requires three steps:

1. **Define the gesture detector** in `core/gestures.py`. Write a function that accepts one or two `hand_landmarks` objects and returns `True` when the gesture signature matches. Use the helper functions in `utils/math_helpers.py` for distance calculations and finger state queries.

2. **Register the technique** in the `TECHNIQUE_INFO` dictionary and add a call to your detector inside `detect_active_technique()`, respecting the priority order (more specific gestures should be evaluated first to avoid false matches with broader ones).

3. **Implement the visual effect** in `core/effects.py`. Add a new method to `EffectGenerator` that draws onto the frame buffer. You can use `_draw_silhouette_particles()` as a base for point-cloud effects, or write custom rendering logic with OpenCV drawing primitives.

For physics-driven effects, instantiate forces through `core/physics.py` and pass the shared `PhysicsParticleSystem` instance from the vision engine.
