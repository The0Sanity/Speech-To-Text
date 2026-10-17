"""Sistem gereksinimleri ve harici bagimliliklar icin otomatik on yukleyici (Bootstrapper)."""

import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from src.audio_processor import find_ffmpeg, find_ffprobe
from src.config import BASE_DIR

# Windows 64-bit resmi gyan.dev static essentials surumu
DEFAULT_FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
# Yedek GitHub mirror
FALLBACK_FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"


class DependencyBootstrapper:
    """Uygulama bagimliliklarini (FFmpeg vb.) denetleyen ve gerektiginde otomatik kuran yonetici."""

    def __init__(self, custom_dir: Optional[Path] = None):
        self._custom_dir = custom_dir

    def get_custom_bin_dir(self) -> Path:
        """Kullaniciya ait ozel yurutulebilir ikili dosya dizinini doner."""
        if self._custom_dir:
            return self._custom_dir

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            bin_dir = Path(local_appdata) / "SpeechToText" / "bin"
        else:
            bin_dir = BASE_DIR / "bin"

        bin_dir.mkdir(parents=True, exist_ok=True)
        return bin_dir

    def register_bin_path(self) -> None:
        """Ozel bin dizinini calisan surecin PATH degiskenine ekler."""
        bin_dir = str(self.get_custom_bin_dir())
        current_path = os.environ.get("PATH", "")
        if bin_dir not in current_path:
            os.environ["PATH"] = bin_dir + os.pathsep + current_path

    def check_ffmpeg_status(self) -> Dict[str, Any]:
        """Sistemdeki veya ozel dizindeki FFmpeg durumunu sorgular."""
        self.register_bin_path()
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            return {
                "installed": False,
                "path": None,
                "version": None,
                "has_ffprobe": False,
            }

        version_str = None
        try:
            res = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0] if res.stdout else ""
                version_str = first_line.replace("ffmpeg version", "").strip().split(" ")[0]
        except Exception:
            version_str = "Bilinmiyor"

        ffprobe_path = find_ffprobe()
        return {
            "installed": True,
            "path": ffmpeg_path,
            "version": version_str,
            "has_ffprobe": bool(ffprobe_path),
        }

    def download_and_extract_ffmpeg(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
        download_url: Optional[str] = None,
    ) -> bool:
        """FFmpeg static zip arsivini indirip ozel bin dizinine ayiklar."""
        bin_dir = self.get_custom_bin_dir()
        temp_zip = bin_dir / "ffmpeg_temp.zip"
        target_ffmpeg = bin_dir / "ffmpeg.exe"
        target_ffprobe = bin_dir / "ffprobe.exe"

        url = download_url or DEFAULT_FFMPEG_URL

        def report(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            report(0.05, "Baglanti kuruluyor...")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SpeechToText-Bootstrapper/1.0"},
            )

            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_zip, "wb") as out_f:
                total_size = resp.getheader("Content-Length")
                total_bytes = int(total_size) if total_size and total_size.isdigit() else 0
                downloaded = 0
                chunk_size = 65536

                while True:
                    if cancel_event and cancel_event.is_set():
                        report(0.0, "Indirme kullanici tarafindan iptal edildi.")
                        if temp_zip.exists():
                            temp_zip.unlink(missing_ok=True)
                        return False

                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)

                    if total_bytes > 0:
                        pct = min(0.85, 0.05 + 0.80 * (downloaded / total_bytes))
                        mb_down = downloaded / (1024 * 1024)
                        mb_total = total_bytes / (1024 * 1024)
                        report(pct, f"Indiriliyor: {mb_down:.1f} / {mb_total:.1f} MB (%{int(pct*100)})")
                    else:
                        mb_down = downloaded / (1024 * 1024)
                        report(0.5, f"Indiriliyor: {mb_down:.1f} MB")

            report(0.88, "Arsiv ayiklaniyor...")
            # Zip icinden ffmpeg.exe ve ffprobe.exe dosyalarini bulup cikar
            with zipfile.ZipFile(temp_zip, "r") as zf:
                for member in zf.namelist():
                    name_lower = member.lower()
                    if name_lower.endswith("ffmpeg.exe"):
                        with zf.open(member) as source, open(target_ffmpeg, "wb") as dest:
                            shutil.copyfileobj(source, dest)
                    elif name_lower.endswith("ffprobe.exe"):
                        with zf.open(member) as source, open(target_ffprobe, "wb") as dest:
                            shutil.copyfileobj(source, dest)

            if temp_zip.exists():
                temp_zip.unlink(missing_ok=True)

            self.register_bin_path()

            if target_ffmpeg.is_file():
                report(1.0, "FFmpeg basariyla kuruldu.")
                return True
            else:
                report(0.0, "Ayiklama sonrasinda ffmpeg.exe bulunamadi.")
                return False

        except Exception as e:
            if temp_zip.exists():
                temp_zip.unlink(missing_ok=True)
            report(0.0, f"Hata olustu: {e}")
            return False
