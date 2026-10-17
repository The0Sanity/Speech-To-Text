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

    # 2. Bootstrapper / Uygulama ozel bin dizini
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        app_bin = Path(local_appdata) / "SpeechToText" / "bin" / "ffmpeg.exe"
        if app_bin.is_file():
            bin_dir = str(app_bin.parent)
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return str(app_bin)

    from src.config import BASE_DIR
    local_bin = BASE_DIR / "bin" / "ffmpeg.exe"
    if local_bin.is_file():
        bin_dir = str(local_bin.parent)
        if bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        return str(local_bin)

    # 3. WinGet Link dizini
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


def build_ffmpeg_filter_string(
    enable_loudnorm: bool = True,
    highpass_hz: int = 80,
    lowpass_hz: int = 7600,
    target_lufs: float = -16.0,
    target_tp: float = -1.5,
    target_lra: float = 11.0,
) -> str:
    """ASR için optimize edilmiş FFmpeg ses filtre zincirini oluşturur.
    
    Örnek:
        "highpass=f=80,lowpass=f=7600,loudnorm=I=-16:TP=-1.5:LRA=11"
    """
    filters = []
    if highpass_hz > 0:
        filters.append(f"highpass=f={highpass_hz}")
    if lowpass_hz > 0:
        filters.append(f"lowpass=f={lowpass_hz}")
    if enable_loudnorm:
        lufs_str = f"{int(target_lufs)}" if float(target_lufs).is_integer() else f"{target_lufs}"
        tp_str = f"{int(target_tp)}" if float(target_tp).is_integer() else f"{target_tp}"
        lra_str = f"{int(target_lra)}" if float(target_lra).is_integer() else f"{target_lra}"
        filters.append(f"loudnorm=I={lufs_str}:TP={tp_str}:LRA={lra_str}")
    return ",".join(filters)


def extract_audio_to_wav(
    input_file: str,
    output_wav_path: Optional[str] = None,
    sample_rate: int = 16000,
    normalize_loudness: bool = True,
    apply_bandpass: bool = True,
) -> str:
    """Herhangi bir video/ses dosyasını 16kHz mono 16-bit PCM WAV formatına dönüştürür.
    
    EBU R128 (-16 LUFS) normalizasyonu ve 80Hz-7600Hz bant filtreleme uygulayarak
    Whisper ve Diarization için en yüksek sinyal kalitesini sağlar.
    """
    ffmpeg_exe = find_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg bulunamadı! Lütfen FFmpeg'in kurulu olduğundan emin olun.")

    if not output_wav_path:
        unique_name = f"audio_{uuid.uuid4().hex[:8]}.wav"
        output_wav_path = str(TEMP_DIR / unique_name)

    # Temel dönüştürme komutu
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_file,
        "-vn",
        "-ac", "1",
        "-ar", str(sample_rate),
    ]

    # Ses filtreleri (EBU R128 + Bandpass)
    filter_chain = build_ffmpeg_filter_string(
        enable_loudnorm=normalize_loudness,
        highpass_hz=80 if apply_bandpass else 0,
        lowpass_hz=7600 if apply_bandpass else 0,
    )
    if filter_chain:
        cmd.extend(["-af", filter_chain])

    cmd.extend(["-c:a", "pcm_s16le", output_wav_path])

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

    # Filtre başarısız olursa güvenli standart dönüştürmeyi dene (fallback)
    if process.returncode != 0 and filter_chain:
        fallback_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", input_file,
            "-vn",
            "-ac", "1",
            "-ar", str(sample_rate),
            "-c:a", "pcm_s16le",
            output_wav_path,
        ]
        process = subprocess.run(
            fallback_cmd,
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
