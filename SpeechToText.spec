# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('settings.json', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'flet',
        'flet.fastapi',
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
        'src.youtube_downloader',
        'src.ui',
        'src.ui.app',
        'src.ui.components',
        'src.ui.style',
        'src.ui.theme',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest'],
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
