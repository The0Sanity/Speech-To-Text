# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

datas = [
    ('settings.json', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Eger flet-windows.zip derleme dizininde mevcutsa flet_desktop altina gom
if os.path.exists('flet-windows.zip'):
    datas.append(('flet-windows.zip', 'flet_desktop/app'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flet',
        'flet.fastapi',
        'flet_desktop',
        'flet_desktop.version',
        'flet_desktop.win_taskbar',
        'rich',
        'rich.progress',
        'faster_whisper',
        'ctranslate2',
        'numpy',
        'scipy',
        'soundfile',
        'yt_dlp',
        'src',
        'src.aligner',
        'src.audio_enhancer',
        'src.audio_processor',
        'src.config',
        'src.diarizer',
        'src.exporter',
        'src.itn',
        'src.text_postprocessor',
        'src.transcriber',
        'src.updater',
        'src.bootstrapper',
        'src.youtube_downloader',
        'src.ui',
        'src.ui.app',
        'src.ui.components',
        'src.ui.style',
        'src.ui.theme',
        'unittest',
        'unittest.mock',
        'multiprocessing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SpeechToText',
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
)
