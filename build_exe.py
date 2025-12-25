"""
Build script for creating DemonX executable
Uses PyInstaller to create a standalone .exe file
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller"""
    print("[*] Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("[+] PyInstaller installed!")

def build_exe():
    """Build the executable"""
    print("[*] Building DemonX executable...")
    
    # Check for required files
    required_files = ["demonx_complete.py", "config.json"]
    optional_files = ["proxies.txt", "presets.json", "operation_queue.json"]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"[!] Required file not found: {file}")
            return False
    
    # Check if demonx package exists
    if not os.path.exists("demonx") or not os.path.isdir("demonx"):
        print("[!] Warning: demonx package directory not found!")
        print("[!] The executable may not work correctly without the package.")
        response = input("[?] Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return False
    
    # Build data files list
    data_files = ["config.json;."]
    if os.path.exists("proxies.txt"):
        data_files.append("proxies.txt;.")
    if os.path.exists("presets.json"):
        data_files.append("presets.json;.")
    if os.path.exists("operation_queue.json"):
        data_files.append("operation_queue.json;.")
    
    # PyInstaller command - use python -m PyInstaller for better compatibility
    # This ensures PyInstaller is found even if not in PATH
    cmd = [
        sys.executable,  # Use the same Python interpreter
        "-m",
        "PyInstaller",
        "--onefile",  # Single executable file
        "--console",  # Console window
        "--name=DemonX",  # Output name
    ]
    
    # Add data files
    for data_file in data_files:
        cmd.append(f"--add-data={data_file}")
    
    # Hidden imports
    cmd.extend([
        "--hidden-import=discord",
        "--hidden-import=discord.ext",
        "--hidden-import=discord.ext.commands",
        "--hidden-import=aiohttp",
        "--hidden-import=aiohttp.client",
        "--hidden-import=aiohttp.connector",
        "--hidden-import=colorama",
        "--hidden-import=colorama.initialise",
        "--hidden-import=asyncio",
        "--hidden-import=json",
        "--hidden-import=logging",
        # DemonX package modules
        "--hidden-import=demonx",
        "--hidden-import=demonx.config",
        "--hidden-import=demonx.rate_limiter",
        "--hidden-import=demonx.proxy_manager",
        "--hidden-import=demonx.history",
        "--hidden-import=demonx.presets",
        "--hidden-import=demonx.utils",
        "--hidden-import=demonx.operation_queue",
        "--hidden-import=demonx.ui_enhancer",
        # Optional UI enhancements (with fallback)
        "--hidden-import=rich",
        "--hidden-import=rich.console",
        "--hidden-import=rich.text",
        "--hidden-import=rich.align",
        "--hidden-import=rich.panel",
        "--hidden-import=pyfiglet",
    ])
    
    # Collect all dependencies
    cmd.extend([
        "--collect-all=discord",
        "--collect-all=aiohttp",
        "--collect-all=colorama",
        "--collect-submodules=demonx",  # Collect all demonx submodules
        "--noconfirm",  # Overwrite without asking
        "demonx_complete.py"
    ])
    
    try:
        print("[*] Running PyInstaller...")
        print("[*] This may take a few minutes...")
        print(f"[*] Using Python: {sys.executable}")
        print(f"[*] Command: {' '.join(cmd)}")
        # Use shell=False for better cross-platform compatibility
        subprocess.check_call(cmd, shell=False)
        print("\n[+] Build successful!")
        print("[+] Executable location: dist/DemonX.exe")
        
        # Copy to root directory (optional - handle errors gracefully)
        if os.path.exists("dist/DemonX.exe"):
            try:
                # Try to remove existing file if it exists
                if os.path.exists("DemonX.exe"):
                    try:
                        os.remove("DemonX.exe")
                    except (PermissionError, OSError):
                        print("[!] Warning: Cannot remove existing DemonX.exe (file may be in use)")
                        print("[*] Skipping copy - executable is available at dist/DemonX.exe")
                        return True
                
                shutil.copy("dist/DemonX.exe", "DemonX.exe")
                print("[+] Copied to: DemonX.exe")
            except (PermissionError, OSError) as e:
                print(f"[!] Warning: Could not copy to root directory: {e}")
                print("[*] Executable is still available at dist/DemonX.exe")
                return True  # Build succeeded, copy is optional
            
            print("\n[+] Build complete! You can now run DemonX.exe")
            print("[*] Note: Make sure config.json is in the same directory as DemonX.exe")
        else:
            print("[!] Warning: Executable not found in dist/ directory")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Build failed: {e}")
        print("[!] Check the error messages above for details")
        return False
    except Exception as e:
        print(f"\n[!] Unexpected error during build: {e}")
        return False
    
    return True

def clean_build_files():
    """Clean build artifacts"""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["DemonX.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[*] Removed {dir_name}/")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"[*] Removed {file_name}")

def main():
    """Main function"""
    print("=" * 50)
    print("DemonX Executable Builder")
    print("=" * 50)
    print()
    
    # Check if PyInstaller is installed
    if not check_pyinstaller():
        print("[!] PyInstaller not found!")
        install = input("[?] Install PyInstaller? (y/n): ").strip().lower()
        if install == 'y':
            install_pyinstaller()
        else:
            print("[!] Cannot build without PyInstaller!")
            return
    
    # Check if main file exists
    if not os.path.exists("demonx_complete.py"):
        print("[!] demonx_complete.py not found!")
        return
    
    # Check for config.json
    if not os.path.exists("config.json"):
        print("[!] config.json not found!")
        create = input("[?] Create default config.json? (y/n): ").strip().lower()
        if create == 'y':
            default_config = '{"proxy": false, "dry_run": false}'
            with open("config.json", "w") as f:
                f.write(default_config)
            print("[+] Created default config.json")
        else:
            print("[!] Cannot build without config.json!")
            return
    
    # Clean previous builds
    clean = input("[?] Clean previous build files? (y/n): ").strip().lower()
    if clean == 'y':
        clean_build_files()
    
    # Build
    if build_exe():
        print("\n" + "=" * 50)
        print("[+] Build complete!")
        print("[+] You can now run DemonX.exe")
        print("=" * 50)
    else:
        print("\n[!] Build failed. Check errors above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Build cancelled by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")

