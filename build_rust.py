"""
Build script for Rust components
"""
import subprocess
import sys
import os
from pathlib import Path

def check_rust():
    """Check if Rust is installed"""
    try:
        result = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[+] Rust found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("[!] Rust not found!")
        print("[*] Please install Rust from https://rustup.rs/")
        return False
    return False

def build_rust_lib():
    """Build Rust library"""
    print("\n[*] Building Rust library...")
    
    # Build with Python bindings
    cmd = ["cargo", "build", "--release", "--features", "python"]
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print("[+] Rust library built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Build failed: {e}")
        return False
    except FileNotFoundError:
        print("[!] Cargo not found!")
        return False

def install_python_bindings():
    """Install Python bindings"""
    print("\n[*] Installing Python bindings...")
    
    # Use maturin for building Python extensions (better than manual setup)
    try:
        # Check if maturin is installed
        subprocess.run(["maturin", "--version"], capture_output=True, check=True)
        
        # Build and install
        cmd = ["maturin", "develop", "--release", "--features", "python"]
        subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print("[+] Python bindings installed!")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[!] Maturin not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "maturin"], check=True)
            cmd = ["maturin", "develop", "--release", "--features", "python"]
            subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
            print("[+] Python bindings installed!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] Failed to install maturin: {e}")
            print("[*] You can manually install with: pip install maturin")
            return False

def main():
    print("=" * 70)
    print("DemonX Rust Components Builder")
    print("=" * 70)
    
    if not check_rust():
        sys.exit(1)
    
    if not build_rust_lib():
        sys.exit(1)
    
    if not install_python_bindings():
        print("[!] Python bindings installation failed, but library is built")
        print("[*] You can manually install with: maturin develop --release")
    
    print("\n[+] Build complete!")
    print("[*] Rust components are ready to use")

if __name__ == "__main__":
    main()

