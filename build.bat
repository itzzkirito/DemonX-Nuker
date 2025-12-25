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

REM Check if demonx package exists
if not exist "demonx" (
    echo [WARNING] demonx package directory not found!
    echo [WARNING] The executable may not work correctly without the package.
    pause
    exit /b 1
)

REM Build executable
echo.
echo [*] Building DemonX.exe...
echo [*] Including config.json
echo [*] Including demonx package
if exist "proxies.txt" (
    echo [*] Including proxies.txt
)
if exist "presets.json" (
    echo [*] Including presets.json
)
if exist "operation_queue.json" (
    echo [*] Including operation_queue.json
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
    --hidden-import=demonx ^
    --hidden-import=demonx.config ^
    --hidden-import=demonx.rate_limiter ^
    --hidden-import=demonx.proxy_manager ^
    --hidden-import=demonx.history ^
    --hidden-import=demonx.presets ^
    --hidden-import=demonx.utils ^
    --hidden-import=demonx.operation_queue ^
    --hidden-import=demonx.ui_enhancer ^
    --hidden-import=rich ^
    --hidden-import=pyfiglet ^
    --collect-all=discord ^
    --collect-all=aiohttp ^
    --collect-all=colorama ^
    --collect-submodules=demonx ^
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

