@echo off
echo ========================================
echo DemonX Nuker - GUI Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python and add it to PATH
    pause
    exit /b 1
)

REM Check if GUI file exists
if not exist "demonx_gui.py" (
    echo [ERROR] demonx_gui.py not found!
    pause
    exit /b 1
)

echo [*] Starting DemonX GUI...
echo.
python demonx_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start GUI!
    echo Check if all dependencies are installed:
    echo   pip install -r requirements.txt
    echo.
)

pause

