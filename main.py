from core.vision_engine import CursedVision

if __name__ == "__main__":
    try:
        app = CursedVision(camera_index=0)
        app.run()
    except Exception as e:
        print(f"Exception capturada: {e}")
