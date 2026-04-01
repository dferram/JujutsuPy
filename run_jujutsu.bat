@echo off
title JujutsuPy - Vision Engine
echo ==========================================
echo   🔮 JujutsuPy Vision Engine Launcher
echo ==========================================
echo.

:: Verifica si python esta instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta disponible en el PATH.
    pause
    exit /b
)

:: Verifica/crea el entorno virtual
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Creando entorno virtual aislado (venv)...
    python -m venv venv
    
    echo [INFO] Instalando dependencias (puede tardar un poco)...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate.bat
)

:: Descarga automagica del modelo si no existe
IF NOT EXIST "models\hand_landmarker.task" (
    echo [INFO] Descargando modelo de MediaPipe (solo la primera vez, ~7MB)...
    mkdir models 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task' -OutFile 'models\hand_landmarker.task'"
)

echo [INFO] Lanzando el motor de vision...
python main.py

echo.
echo [INFO] Ejecucion finalizada.
pause
