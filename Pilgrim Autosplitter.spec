# -*- mode: python ; coding: utf-8 -*-
# Frozen builds: macOS produces Pilgrim Autosplitter.app; Windows/Linux produce
# dist/Pilgrim Autosplitter/ with the main executable inside (see README).
import sys
from pathlib import Path


def _exe_icon():
    """Platform-appropriate icon; omit if file missing."""
    if sys.platform == 'win32':
        p = Path('resources/icon-windows.ico')
        return str(p) if p.is_file() else None
    p = Path('resources/icon-macos.icns')
    return [str(p)] if p.is_file() else None


# pynput loads platform backends dynamically; list them so frozen Windows
# builds still start the keyboard listener. Darwin backends are harmless extras
# when building on Windows, and help if this onedir spec is used on macOS.
_PYNPUT_HIDDENIMPORTS = [
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'pynput._util.win32',
    'pynput.keyboard._darwin',
    'pynput.mouse._darwin',
    'pynput._util.darwin',
]


a = Analysis(
    ['src/pilgrim_autosplitter.py'],
    pathex=['src'],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=_PYNPUT_HIDDENIMPORTS,
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
    [],
    exclude_binaries=True,
    name='Pilgrim Autosplitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_exe_icon(),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Pilgrim Autosplitter',
)

if sys.platform == 'darwin':
    _plist_icon = (
        'resources/icon-macos.icns'
        if Path('resources/icon-macos.icns').is_file()
        else None
    )
    app = BUNDLE(
        coll,
        name='Pilgrim Autosplitter.app',
        icon=_plist_icon,
        bundle_identifier='org.pilgrimtabby.PilgrimAutosplitter',
        info_plist={
            'NSCameraUsageDescription': (
                'Pilgrim Autosplitter captures video from your chosen device to compare '
                'the feed with split images and drive autosplits.'
            ),
        },
    )
