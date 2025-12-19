@echo off
echo ========================================
echo DemonX Nuker - Launcher
echo ========================================
echo.
echo [1] Run DemonX Complete (CLI)
echo [2] Run DemonX GUI (Graphical)
echo [3] Install Dependencies
echo [0] Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" (
    python demonx_complete.py
) else if "%choice%"=="2" (
    python demonx_gui.py
) else if "%choice%"=="3" (
    pip install -r requirements.txt
    pause
) else if "%choice%"=="0" (
    exit
) else (
    echo Invalid choice!
    pause
)

