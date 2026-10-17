"""Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma Aracı Başlatıcısı."""

import os
import sys
from pathlib import Path

# Proje ana dizinini sys.path'e ekle
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# FFmpeg yolunu dinamik olarak tespit et ve PATH'e ekle
from src.audio_processor import find_ffmpeg

ffmpeg_exe = find_ffmpeg()
if ffmpeg_exe:
    ffmpeg_dir = str(Path(ffmpeg_exe).parent)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

from src.ui.app import run_gui


def main():
    """Uygulama giriş noktası."""
    try:
        run_gui()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("\nUygulama çalışırken beklenmeyen bir hata oluştu. Çıkmak için Enter'a basın...")


if __name__ == "__main__":
    main()
