"""YouTube üzerinden ses indirme ve metaveri çekme modülü (yt-dlp + FFmpeg).

Bot algılama (Sign in to confirm you're not a bot) engellerini aşmak için
mobil istemci (android, ios, mweb) spoofing ve otomatik tarayıcı çerezi
yedekleme mekanizmasına sahiptir.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Kurumsal / Okul SSL sertifika uyumluluğu
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import yt_dlp

from src.audio_processor import find_ffmpeg, format_time
from src.config import TEMP_DIR

YOUTUBE_URL_REGEX = re.compile(
    r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)


def clean_error_message(err: Any) -> str:
    """Hata mesajındaki ANSI konsol renk kodlarını ve gereksiz URL kalabalığını temizler."""
    text = str(err)
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    text = re.sub(r"\[[0-9;]*m", "", text)
    # Temizle
    return text.strip()


def is_valid_youtube_url(url: str) -> bool:
    """Girilen metnin geçerli bir YouTube URL'si olup olmadığını denetler."""
    if not url:
        return False
    return bool(YOUTUBE_URL_REGEX.search(url.strip()))


def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL'sinden 11 karakterlik video ID'sini ayıklar."""
    match = YOUTUBE_URL_REGEX.search(url.strip())
    if match:
        return match.group(5)
    return None


def _get_base_extractor_args() -> Dict[str, Any]:
    """Bot tespitini baypas eden optimize edilmiş YouTube oynatıcı istemcileri."""
    return {
        "youtube": {
            "player_client": ["android", "ios", "mweb"],
        }
    }


def get_youtube_video_info(url: str) -> Dict[str, Any]:
    """
    Video dosyasını indirmeden başlık, süre ve kanal adı gibi temel bilgileri çeker.
    Bot engeline karşı mobil istemci ve tarayıcı çerezi yedeklerini dener.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Geçersiz YouTube URL'si! Lütfen geçerli bir bağlantı giriniz.")

    url = url.strip()

    # Denenecek yapılandırma stratejileri:
    # 1. Mobil İstemciler (Android / iOS / MWeb - En başarılı bot baypas yöntemi)
    # 2. Edge Çerezleri
    # 3. Chrome Çerezleri
    # 4. Firefox Çerezleri
    strategies: List[Dict[str, Any]] = [
        {"extractor_args": _get_base_extractor_args()},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("edge",)},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("chrome",)},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("firefox",)},
    ]

    last_error: Optional[Exception] = None

    for strat in strategies:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "nocheckcertificate": True,
        }
        ydl_opts.update(strat)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration_sec = float(info.get("duration") or 0.0)

                return {
                    "title": info.get("title", "YouTube Videosu"),
                    "channel": info.get("uploader") or info.get("channel", "Bilinmeyen Kanal"),
                    "duration_seconds": round(duration_sec, 2),
                    "duration_formatted": format_time(duration_sec),
                    "url": url,
                    "video_id": info.get("id", extract_video_id(url)),
                    "file_name": f"{info.get('title', 'YouTube')}.mp3",
                    "file_size_mb": round((duration_sec * 128 / 8) / 1024, 2),
                }
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(clean_error_message(last_error))


def download_youtube_audio(
    url: str,
    output_wav_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    YouTube videosundan yalnızca ses akışını (audio-only) indirir ve 16kHz mono WAV biçimine dönüştürür.
    Bot korumasını mobil istemcilerle aşar.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Geçersiz YouTube bağlantısı!")

    url = url.strip()
    ffmpeg_bin = find_ffmpeg()
    ffmpeg_dir = str(Path(ffmpeg_bin).parent) if ffmpeg_bin else None

    # Benzersiz geçici dosya adı
    unique_id = uuid.uuid4().hex[:8]
    if not output_wav_path:
        target_wav = str(TEMP_DIR / f"yt_{unique_id}.wav")
    else:
        target_wav = output_wav_path

    temp_template = str(TEMP_DIR / f"yt_dl_{unique_id}.%(ext)s")

    def ydl_progress_hook(d):
        if progress_callback and d.get("status") == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total_bytes > 0:
                pct = downloaded / total_bytes
                progress_callback(pct * 0.5, f"YouTube'dan ses indiriliyor... %{int(pct * 100)}")
            else:
                progress_callback(0.2, "YouTube'dan ses indiriliyor...")
        elif progress_callback and d.get("status") == "finished":
            progress_callback(0.5, "Ses indirildi, 16kHz WAV formatına dönüştürülüyor...")

    strategies: List[Dict[str, Any]] = [
        {"extractor_args": _get_base_extractor_args()},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("edge",)},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("chrome",)},
        {"extractor_args": _get_base_extractor_args(), "cookiesfrombrowser": ("firefox",)},
    ]

    last_error: Optional[Exception] = None

    for strat in strategies:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_template,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [ydl_progress_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
            "postprocessor_args": [
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
            ],
        }
        if ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = ffmpeg_dir
        ydl_opts.update(strat)

        try:
            if progress_callback:
                progress_callback(0.05, "YouTube video akışı başlatılıyor...")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration_sec = float(info.get("duration") or 0.0)

                meta = {
                    "title": info.get("title", "YouTube Videosu"),
                    "channel": info.get("uploader") or info.get("channel", "Bilinmeyen Kanal"),
                    "duration_seconds": round(duration_sec, 2),
                    "duration_formatted": format_time(duration_sec),
                    "url": url,
                    "video_id": info.get("id", ""),
                    "file_name": f"{info.get('title', 'YouTube')}.wav",
                    "file_size_mb": 0.0,
                }

            # İndirilen ve dönüştürülen wav dosyasını bul ve target_wav'e taşı
            downloaded_wav = str(TEMP_DIR / f"yt_dl_{unique_id}.wav")
            if os.path.isfile(downloaded_wav):
                if downloaded_wav != target_wav:
                    if os.path.exists(target_wav):
                        os.remove(target_wav)
                    os.rename(downloaded_wav, target_wav)
                file_size = os.path.getsize(target_wav) / (1024 * 1024)
                meta["file_size_mb"] = round(file_size, 2)
                return target_wav, meta

            # Alternatif: dosya farklı bir uzantıyla indirilmişse
            for candidate in TEMP_DIR.glob(f"yt_dl_{unique_id}.*"):
                if candidate.is_file():
                    from src.audio_processor import extract_audio_to_wav
                    wav_res = extract_audio_to_wav(str(candidate), target_wav)
                    try:
                        os.remove(candidate)
                    except Exception:
                        pass
                    file_size = os.path.getsize(wav_res) / (1024 * 1024)
                    meta["file_size_mb"] = round(file_size, 2)
                    return wav_res, meta

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"YouTube indirme hatası: {clean_error_message(last_error)}")
