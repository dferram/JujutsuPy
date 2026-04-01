@echo off
title JujutsuPy - Motor de Cursed Vision
echo ==========================================
echo   🔮 JujutsuPy Vision Engine Launcher
echo ==========================================
echo.

:: Verifica si python esta instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH del sistema.
    echo Por favor instala Python desde python.org y marcan "Add Python to PATH".
    pause
    exit /b
)

:: Verifica si existe el entorno virtual
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] No se encontro el entorno virtual (venv).
    echo [INFO] Creando un entorno aislado para el proyecto...
    python -m venv venv
    
    echo [INFO] Activando entorno e instalando dependencias. Esto tomara un momento...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [INFO] ¡Instalacion completa!
    echo.
) ELSE (
    echo [INFO] Activando entorno virtual...
    call venv\Scripts\activate.bat
)

echo [INFO] Lanzando Cursed Vision...
python main.py

echo.
echo [INFO] Script finalizado.
pause
