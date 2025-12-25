"""
PyInstaller spec file generator for DemonX
Creates a proper .spec file for building the executable
"""

import os

spec_content = """# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Collect all dependencies
datas = [('config.json', '.')]
binaries = []
hiddenimports = [
    'discord',
    'discord.ext',
    'discord.ext.commands',
    'aiohttp',
    'aiohttp.client',
    'aiohttp.connector',
    'colorama',
    'colorama.initialise',
    'asyncio',
    'json',
    'logging',
]

# Collect all data files
import os
if os.path.exists('proxies.txt'):
    datas.append(('proxies.txt', '.'))
if os.path.exists('presets.json'):
    datas.append(('presets.json', '.'))

# Collect all package data
tmp_ret = collect_all('discord')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('aiohttp')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('colorama')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['demonx_complete.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DemonX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""

def create_spec():
    """Create the .spec file"""
    with open("DemonX.spec", "w") as f:
        f.write(spec_content)
    print("[+] Created DemonX.spec")
    print("[*] To build, run: pyinstaller DemonX.spec")

if __name__ == "__main__":
    create_spec()

