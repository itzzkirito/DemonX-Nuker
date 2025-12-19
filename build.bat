@echo off
echo ========================================
echo DemonX Executable Builder
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

REM Install PyInstaller if needed
echo [*] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [*] Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        pause
        exit /b 1
    )
)

REM Build executable
echo.
echo [*] Building DemonX.exe...
echo [*] Including config.json
if exist "proxies.txt" (
    echo [*] Including proxies.txt
)
if exist "presets.json" (
    echo [*] Including presets.json
)
echo.

python -m PyInstaller --onefile --console --name=DemonX ^
    --add-data="config.json;." ^
    --hidden-import=discord ^
    --hidden-import=discord.ext ^
    --hidden-import=discord.ext.commands ^
    --hidden-import=aiohttp ^
    --hidden-import=aiohttp.client ^
    --hidden-import=aiohttp.connector ^
    --hidden-import=colorama ^
    --hidden-import=colorama.initialise ^
    --hidden-import=asyncio ^
    --hidden-import=json ^
    --hidden-import=logging ^
    --collect-all=discord ^
    --collect-all=aiohttp ^
    --collect-all=colorama ^
    --noconfirm ^
    demonx_complete.py

REM Note: proxies.txt and presets.json are optional and loaded at runtime
REM They don't need to be bundled if users can add them separately

if exist "dist\DemonX.exe" (
    echo.
    echo [+] Build successful!
    echo [+] Executable: dist\DemonX.exe
    copy "dist\DemonX.exe" "DemonX.exe" >nul
    echo [+] Copied to: DemonX.exe
    echo.
) else (
    echo.
    echo [!] Build failed!
    echo.
)

pause

