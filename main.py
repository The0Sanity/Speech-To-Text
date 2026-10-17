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

# Windows Yüksek DPI (High-DPI) ölçekleme desteğini etkinleştir
if sys.platform == "win32":
    try:
        import ctypes
        # Windows 8.1+ ve Windows 10/11 için Per-Monitor DPI Awareness v2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def main():
    """Uygulama giriş noktası."""
    try:
        if "--version" in sys.argv or "-v" in sys.argv:
            from src.config import APP_NAME, APP_VERSION
            print(f"{APP_NAME} v{APP_VERSION}")
            return

        if "--check-update" in sys.argv:
            from src.updater import AutoUpdater
            updater = AutoUpdater()
            print("Guncellemeler denetleniyor...")
            info = updater.check_for_updates()
            if not info:
                print("Guncelleme denetlenemedi veya ag baglantisi yok.")
            elif info.is_update_available:
                print(f"YENI SURUM MEVCUT: v{info.version} (Mevcut: v{updater.current_version})")
                if info.has_exe_asset:
                    print(f"Indirilebilir .exe varligi: {info.asset_name} ({info.asset_size / (1024*1024):.1f} MB)")
                    print(f"Indirme baglantisi: {info.download_url}")
                else:
                    print("Yeni surum yayinlanmis fakat henuz .exe varligi eklenmemis.")
            else:
                print(f"Uygulamaniz guncel: v{updater.current_version}")
            return

        if "--check" in sys.argv or "--dry-run" in sys.argv:
            import src.aligner
            import src.audio_enhancer
            import src.audio_processor
            import src.config
            import src.diarizer
            import src.exporter
            import src.text_postprocessor
            import src.transcriber
            import src.updater
            import src.youtube_downloader
            import flet as ft
            from src.ui.app import FletSpeechToTextApp
            app = FletSpeechToTextApp()
            print("DOĞRULAMA BAŞARILI: Tüm modüller ve Flet UI başarıyla yüklendi.")
            return

        import flet as ft
        from src.ui.app import run_flet_app
        if hasattr(ft, "run"):
            ft.run(run_flet_app)
        elif hasattr(ft, "app"):
            ft.app(target=run_flet_app)
        else:
            raise RuntimeError("Uyumlu bir Flet çalıştırma metodu (run / app) bulunamadı.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("\nUygulama çalışırken beklenmeyen bir hata oluştu. Çıkmak için Enter'a basın...")


if __name__ == "__main__":
    main()

