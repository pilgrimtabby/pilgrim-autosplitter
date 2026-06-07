# -*- mode: python ; coding: utf-8 -*-
# Single-file Windows build — run PyInstaller on Windows only.
# Output: dist/Pilgrim Autosplitter.exe (self-extracts to TEMP at startup).
from pathlib import Path


def _win_icon():
    p = Path('resources/icon-windows.ico')
    return str(p) if p.is_file() else None


a = Analysis(
    ['src/pilgrim_autosplitter.py'],
    pathex=['src'],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Pilgrim Autosplitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_win_icon(),
)
