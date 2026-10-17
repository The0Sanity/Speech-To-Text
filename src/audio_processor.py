"""Ses ve video dosyalarını işleme, FFmpeg entegrasyonu ve dönüştürme modülü."""

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.config import TEMP_DIR


def find_ffmpeg() -> Optional[str]:
    """FFmpeg çalıştırılabilir dosyasını sistemde veya winget dizininde arar."""
    # 1. Standart PATH kontrolü
    direct = shutil.which("ffmpeg")
    if direct:
        return direct

    # 2. WinGet Link dizini
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        winget_link = Path(local_appdata) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
        if winget_link.is_file():
            return str(winget_link)

        # 3. WinGet Packages altı arama
        packages_dir = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if packages_dir.exists():
            for p in packages_dir.glob("**/ffmpeg.exe"):
                if p.is_file():
                    bin_dir = str(p.parent)
                    if bin_dir not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                    return str(p)

    # 4. Program Files dizinleri
    for pf in [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")]:
        if pf:
            for p in Path(pf).glob("**/ffmpeg.exe"):
                if p.is_file():
                    return str(p)

    return None


def find_ffprobe() -> Optional[str]:
    """FFprobe çalıştırılabilir dosyasını arar."""
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path:
        ffmpeg_dir = Path(ffmpeg_path).parent
        probe_path = ffmpeg_dir / "ffprobe.exe"
        if probe_path.is_file():
            return str(probe_path)

    direct = shutil.which("ffprobe")
    if direct:
        return direct

    return None


def get_media_info(file_path: str) -> Dict[str, any]:
    """Medya dosyasının süresini, boyutunu ve ses kanallarını döndürür."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

    file_size_mb = path.stat().st_size / (1024 * 1024)
    duration = 0.0
    channels = 0
    sample_rate = 0

    ffprobe = find_ffprobe()
    if ffprobe:
        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))

            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    channels = int(stream.get("channels", 1))
                    sample_rate = int(stream.get("sample_rate", 16000))
                    break
        except Exception as e:
            print(f"FFprobe analiz uyarısı: {e}")

    return {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_size_mb": round(file_size_mb, 2),
        "duration_seconds": round(duration, 2),
        "duration_formatted": format_time(duration),
        "channels": channels,
        "sample_rate": sample_rate,
    }


def format_time(seconds: float) -> str:
    """Saniyeyi HH:MM:SS veya MM:SS biçimine dönüştürür."""
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def extract_audio_to_wav(
    input_file: str,
    output_wav_path: Optional[str] = None,
    sample_rate: int = 16000
) -> str:
    """Herhangi bir video/ses dosyasını 16kHz mono 16-bit PCM WAV formatına dönüştürür.
    
    Bu format Whisper ve Diarization motorları için endüstri standardıdır.
    """
    ffmpeg_exe = find_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg bulunamadı! Lütfen FFmpeg'in kurulu olduğundan emin olun.")

    if not output_wav_path:
        unique_name = f"audio_{uuid.uuid4().hex[:8]}.wav"
        output_wav_path = str(TEMP_DIR / unique_name)

    # ffmpeg parametreleri:
    # -y: Mevcut dosyanın üzerine yaz
    # -i: Girdi dosyası
    # -vn: Varsa video akışını göz ardı et
    # -ac 1: Tek kanal (mono)
    # -ar: Örnekleme hızı (16000 Hz)
    # -c:a pcm_s16le: 16-bit signed PCM codec
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_file,
        "-vn",
        "-ac", "1",
        "-ar", str(sample_rate),
        "-c:a", "pcm_s16le",
        output_wav_path,
    ]

    # Windows'ta konsol penceresi açılmasını engellemek için startupinfo
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        text=True,
    )

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg ses dönüştürme hatası: {process.stderr}")

    return output_wav_path


def cleanup_temp_file(file_path: Optional[str]) -> None:
    """Geçici dosyayı temizler."""
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Geçici dosya silinemedi: {e}")
