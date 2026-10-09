# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for MP4×MP3 Loop Merger
# Run with: pyinstaller build.spec

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Data files ──────────────────────────────────────────────────────────────
datas = [
    # FFmpeg binaries
    (os.path.join('resources', 'ffmpeg', 'ffmpeg.exe'),  '.'),
    (os.path.join('resources', 'ffmpeg', 'ffprobe.exe'), '.'),
    # Qt StyleSheet
    (os.path.join('src', 'styles', 'theme.qss'), os.path.join('src', 'styles')),
    # App icon
    (os.path.join('resources', 'icons', 'app.ico'), os.path.join('resources', 'icons')),
]

# ── Hidden imports ────────────────────────────────────────────────────────────
hiddenimports = [
    'psutil',
    'psutil._pswindows',
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'src.core.models',
    'src.core.ffmpeg_runner',
    'src.core.batch_worker',
    'src.core.hardware_detector',
    'src.utils.ffprobe_utils',
    'src.utils.path_utils',
    'src.utils.media_matcher',
    'src.widgets.log_panel',
    'src.widgets.pair_row_widget',
    'src.widgets.encoding_selector',
    'src.pages.single_page',
    'src.pages.batch_page',
    'src.pages.device_info_page',
    'src.pages.guide_page',
    'src.app_window',
]

a = Analysis(
    [os.path.join('src', 'main.py')],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL',
        'IPython', 'jupyter', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── --onedir build (faster startup, easier to update FFmpeg) ─────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MuliaMixing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('resources', 'icons', 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MuliaMixing',
)
