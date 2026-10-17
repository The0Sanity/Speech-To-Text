"""Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma Aracı Başlatıcısı."""

import builtins
import os
import sys
from pathlib import Path

# Donmus (.exe) ve consolesuz ortamlarda exit() cagrilari icin guvenlik onlemi
if not hasattr(builtins, "exit"):
    builtins.exit = sys.exit
if not hasattr(builtins, "quit"):
    builtins.quit = sys.exit

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

def ensure_flet_icons_available() -> None:
    """Flet materyal ve cupertino ikon kaynaklarinin varligini dogrular ve calisma zamaninda korur.

    PyInstaller tek-dosya modunda veya kisitli dosya sistemi izinlerinde
    flet/controls/material/icons.json dosyasinin okunamamasi durumunda
    uygulamanin FileNotFoundError ile cokmesini engeller ve guvenli yedek
    esleme saglar.
    """
    class SafeIconDict(dict):
        def __getitem__(self, key):
            return super().get(key, 0xe000)

        def __contains__(self, key):
            return True

    # 1. Material Icons korumasi
    try:
        from flet.controls.material.icons import _IconsProxy

        orig_mat_load = getattr(_IconsProxy, "_load", None)
        if callable(orig_mat_load) and not getattr(_IconsProxy, "_is_safe_patched", False):
            def safe_mat_load(self):
                if self._map is not None:
                    return
                try:
                    orig_mat_load(self)
                except Exception:
                    self._map = SafeIconDict({
                        "CODE": 0xe174,
                        "COPY": 0xe197,
                        "CONTENT_COPY": 0xe197,
                        "SETTINGS": 0xe57f,
                        "FOLDER": 0xe2a3,
                        "AUDIO_FILE": 0xe9e5,
                        "PLAY_ARROW": 0xe4d8,
                        "PAUSE": 0xe487,
                        "STOP": 0xe5bb,
                        "REFRESH": 0xe526,
                        "SEARCH": 0xe567,
                        "DELETE": 0xe1bb,
                        "DOWNLOAD": 0xe204,
                        "INFO": 0xe88e,
                        "WARNING": 0xe002,
                        "ERROR": 0xe000,
                        "CHECK": 0xe5ca,
                        "CLOSE": 0xe5cd,
                    })

            _IconsProxy._load = safe_mat_load
            _IconsProxy._is_safe_patched = True
    except Exception:
        pass

    # 2. Cupertino Icons korumasi
    try:
        from flet.controls.cupertino.cupertino_icons import _CupertinoIconsProxy

        orig_cup_load = getattr(_CupertinoIconsProxy, "_load", None)
        if callable(orig_cup_load) and not getattr(_CupertinoIconsProxy, "_is_safe_patched", False):
            def safe_cup_load(self):
                if self._map is not None:
                    return
                try:
                    orig_cup_load(self)
                except Exception:
                    self._map = SafeIconDict()

            _CupertinoIconsProxy._load = safe_cup_load
            _CupertinoIconsProxy._is_safe_patched = True
    except Exception:
        pass

# Baslangicta ikon korumasini derhal devreye al
ensure_flet_icons_available()

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
        err_msg = traceback.format_exc()
        try:
            from src.config import get_base_dir
            crash_log = get_base_dir() / "crash.log"
        except Exception:
            crash_log = Path("crash.log")

        try:
            with open(crash_log, "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass

        traceback.print_exc()

        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            try:
                input("\nUygulama calisirken beklenmeyen bir hata olustu. Cikmak icin Enter'a basin...")
            except Exception:
                pass
        else:
            if sys.platform == "win32":
                try:
                    import ctypes
                    short_err = str(e)
                    box_text = f"Uygulama baslatilirken bir hata olustu:\n\n{short_err}\n\nAyrintili kayit: {crash_log}"
                    ctypes.windll.user32.MessageBoxW(0, box_text, "SesMetin Hata", 0x10)
                except Exception:
                    pass


if __name__ == "__main__":
    main()

