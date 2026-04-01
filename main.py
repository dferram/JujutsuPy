"""
JujutsuPy — Motor de Visión por Computadora con Jujutsu Kaisen
Punto de entrada principal de la aplicación.
"""

from core.vision_engine import CursedVision


def main():
    try:
        app = CursedVision(camera_index=0)
        app.run()
    except RuntimeError as e:
        print(f"❌ Error de cámara: {e}")
    except KeyboardInterrupt:
        print("\n🔮 Cerrando JujutsuPy...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    main()
