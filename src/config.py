"""Uygulama yapılandırma ve ayarlar yöneticisi."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Windows kurumsal / okul SSL sertifika uyumluluğu için truststore enjeksiyonu
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

def get_base_dir() -> Path:
    """Uygulamanin kalici calisma dizinini tespit eder.

    PyInstaller tek-dosya (one-file) kipinde __file__ gecici _MEIPASS
    dizinini gosterir. Verilerin uygulama kapandiginda kaybolmamasi icin
    calistirilabilir dosyanin (sys.executable) bulundugu gercek dizin alinir.
    Eger bu dizin salt-okunur ise, %LOCALAPPDATA%/SpeechToText dizinine guvenli
    gecis yapilir.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        test_file = exe_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            return exe_dir
        except (PermissionError, OSError):
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                fallback = Path(local_appdata) / "SpeechToText"
                fallback.mkdir(parents=True, exist_ok=True)
                return fallback
            return exe_dir
    return Path(__file__).resolve().parent.parent


def get_config_dir() -> Path:
    """Kullanıcı yapılandırma dizinini döndürür (OS standartlarına uygun)."""
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        cfg_dir = Path(appdata) / "SesMetinPro"
    else:
        cfg_dir = Path.home() / ".config" / "sesmetinpro"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


# Temel Dizin Yollari
BASE_DIR = get_base_dir()
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
SETTINGS_FILE = CONFIG_FILE  # Geriye dönük uyumluluk takma adı

# Uygulama Sürümü ve Depo Bilgileri
APP_VERSION = "1.1.5"
APP_NAME = "SesMetin Pro"
GITHUB_REPO_OWNER = "The0Sanity"
GITHUB_REPO_NAME = "Speech-To-Text"
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

# Dizinlerin varlığını garantiye al
for directory in [MODELS_DIR, OUTPUTS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG: Dict[str, Any] = {
    "model_size": "small",         # "tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"
    "hardware_mode": "auto",       # "auto", "cuda", "cpu"
    "language": "tr",              # Varsayılan Türkçe
    "speaker_prefix": "X",         # "X1", "X2" formatı için
    "min_speakers": None,          # Otomatik tespit veya tamsayı
    "max_speakers": None,
    "hf_token": "",                # Hugging Face token (Pyannote için opsiyonel)
    "use_pyannote": False,         # Token varsa Pyannote kullanımı
    "theme": "dark",               # "dark", "light", "system"
    "auto_merge_gap": 1.5,         # Aynı konuşmacının ardışık cümlelerini birleştirme eşiği (sn)
    "enhance_audio": True,         # Ön-işleme ses iyileştirme (Gürültü kapısı + Filtre + Normalizasyon)
    "enable_acoustic_preprocessing": True, # Akustik VAD ve spektral frekans vurgulama
    "normalize_loudness": True,    # EBU R128 Loudness normalizasyonu (-16 LUFS)
    "postprocess_text": True,      # Türkçe metin temizleme ve halüsinasyon filtresi
    "enable_turkish_post_processing": True, # Türkçe fonetik ve morfolojik düzeltme
    "apply_itn": True,             # Türkçe Ters Metin Normalizasyonu (Sayı, Yüzde, Para)
    "clean_disfluencies": True,    # Dolgu sözcük temizliği (ııı, eee, şey, yani)
    "rolling_prompt": True,        # Segmentler arası hareketli bağlam istemi (Rolling Context)
    "vocabulary_bias": "",         # Özel terim ve sözlük ipuçları
    "beam_size": 5,                # Arama genişliği (Yüksek doğruluk)
    "vad_sensitivity": "high",     # "high" (Sessiz ve hızlı sesleri kaçırmaz), "normal"
    "last_input_dir": str(BASE_DIR),
    "last_output_dir": str(OUTPUTS_DIR),
    "last_seen_version": APP_VERSION,
    "postponed_update": None,
    "pending_patch_notes": "",
}


def load_settings() -> Dict[str, Any]:
    """Yapılandırma dosyasından ayarları yükler, yoksa varsayılanı kaydeder.
    Eski BASE_DIR / settings.json varsa taşır ve eski dosyayı siler."""
    legacy_file = BASE_DIR / "settings.json"
    legacy_data = None
    if legacy_file.exists():
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                legacy_data = json.load(f)
            try:
                legacy_file.unlink()
            except OSError:
                pass
        except Exception:
            pass

    if not CONFIG_FILE.exists():
        initial = DEFAULT_CONFIG.copy()
        if legacy_data and isinstance(legacy_data, dict):
            initial.update(legacy_data)
        save_settings(initial)
        return initial

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            if legacy_data and isinstance(legacy_data, dict):
                merged.update(legacy_data)
                save_settings(merged)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_settings(settings: Dict[str, Any]) -> None:
    """Ayarları OS standardındaki config.json dosyasına kaydeder."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ayar kaydetme hatası: {e}")
