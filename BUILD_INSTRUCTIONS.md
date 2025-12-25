# Building DemonX Executable

## Quick Build (Windows)

### Method 1: Using build.bat (Easiest)
```bash
build.bat
```

### Method 2: Using Python script
```bash
python build_exe.py
```

### Method 3: Manual PyInstaller
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --console --name=DemonX demonx_complete.py
```

## Detailed Build Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Build Options

#### Basic Build
```bash
pyinstaller --onefile --console --name=DemonX demonx_complete.py
```

#### Advanced Build (Recommended)
```bash
pyinstaller --onefile --console --name=DemonX ^
    --add-data="config.json;." ^
    --hidden-import=discord ^
    --hidden-import=discord.ext.commands ^
    --hidden-import=aiohttp ^
    --hidden-import=colorama ^
    --collect-all=discord ^
    --collect-all=aiohttp ^
    --noconfirm ^
    demonx_complete.py
```

#### Using Spec File
```bash
# Generate spec file
python build_spec.py

# Build using spec
pyinstaller DemonX.spec
```

### 3. Output Location
- Executable: `dist/DemonX.exe`
- Will also be copied to root: `DemonX.exe`

## Build Options Explained

- `--onefile`: Creates a single executable file
- `--console`: Shows console window (remove for GUI)
- `--name=DemonX`: Output filename
- `--add-data`: Include additional files (config.json, etc.)
- `--hidden-import`: Force include modules that PyInstaller might miss
- `--collect-all`: Include all submodules
- `--noconfirm`: Overwrite without asking

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Add missing modules to `--hidden-import`

### Issue: Large file size
**Solution**: Use `--exclude-module` to remove unused modules

### Issue: Antivirus flags the exe
**Solution**: This is normal for PyInstaller builds. Add exception or use code signing.

### Issue: Missing dependencies
**Solution**: Ensure all packages in requirements.txt are installed

## File Size Optimization

To reduce executable size:
```bash
pyinstaller --onefile --console --name=DemonX ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=pandas ^
    demonx_complete.py
```

## Adding Icon

1. Create or download `icon.ico`
2. Add to build command:
```bash
pyinstaller --onefile --console --name=DemonX --icon=icon.ico demonx_complete.py
```

## Testing the Executable

1. Run `DemonX.exe`
2. Check if it starts correctly
3. Test all features
4. Verify config.json is accessible

## Notes

- First build may take several minutes
- Executable size: ~50-100MB (includes Python runtime)
- Antivirus may flag as suspicious (false positive)
- Works on Windows 7+ (64-bit recommended)

