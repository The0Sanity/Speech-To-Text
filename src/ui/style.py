"""Masaüstü arayüzü renk paletleri, temalar, tipografi ve konuşmacı stilleri."""

import hashlib
from typing import Dict, Tuple

# Konuşmacı rozet renkleri (Arka plan rengi, Yazı rengi)
SPEAKER_COLORS: Dict[str, Tuple[str, str]] = {
    "X1": ("#10b981", "#ffffff"),  # Zümrüt Yeşili
    "X2": ("#8b5cf6", "#ffffff"),  # Canlı Mor / Violet
    "X3": ("#f59e0b", "#ffffff"),  # Kehribar Sarısı
    "X4": ("#f43f5e", "#ffffff"),  # Gül Kurusu / Kırmızı
    "X5": ("#06b6d4", "#ffffff"),  # Camgöbeği (Cyan)
    "X6": ("#ec4899", "#ffffff"),  # Fuşya / Pembe
    "X7": ("#3b82f6", "#ffffff"),  # Safir Mavisi
    "X8": ("#84cc16", "#ffffff"),  # Limon Yeşili
    "X9": ("#14b8a6", "#ffffff"),  # Turkuaz
    "X10": ("#a855f7", "#ffffff"), # Lavanta
    "X11": ("#eab308", "#ffffff"), # Altın
    "X12": ("#6366f1", "#ffffff"), # İndigo
}

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_app": "#0b0f17",             # Çok koyu lacivert-siyah arka plan
        "bg_card": "#131a26",            # Kart yüzey rengi
        "bg_card_secondary": "#1c2536",  # Vurgulu/ikincil kart yüzeyi
        "bg_card_hover": "#222e42",      # Üzerine gelindiğinde kart rengi
        "border_card": "#232e40",        # İnce kart kenarlık rengi
        "border_highlight": "#3b82f6",   # Aktif/odaklanmış kenarlık
        "accent_primary": "#2563eb",     # Birincil mavi eylem rengi
        "accent_hover": "#1d4ed8",       # Birincil hover
        "accent_soft": "#1e3a8a",        # Yumuşak mavi arka plan
        "text_main": "#f8fafc",          # Açık beyaz ana metin
        "text_muted": "#94a3b8",         # Gri ikincil metin
        "text_subtle": "#64748b",        # Soluk açıklama metni
        "success": "#10b981",            # Yeşil başarı rengi
        "success_hover": "#059669",
        "warning": "#f59e0b",            # Amber uyarı
        "danger": "#ef4444",             # Kırmızı hata
        "danger_hover": "#dc2626",
        "info": "#06b6d4",               # Mavi/Cyan bilgi
        "badge_bg": "#1e293b",
        "input_bg": "#0e141f",           # Girdi kutuları arka planı
        "input_border": "#273447",
        "stepper_active": "#38bdf8",     # Aktif adım rengi
        "stepper_done": "#10b981",       # Tamamlanan adım rengi
        "stepper_pending": "#475569",    # Bekleyen adım rengi
    },
    "light": {
        "bg_app": "#f1f5f9",             # Açık gri/mavi arka plan
        "bg_card": "#ffffff",            # Beyaz kart yüzeyi
        "bg_card_secondary": "#f8fafc",  # Açık ikincil kart
        "bg_card_hover": "#e2e8f0",
        "border_card": "#cbd5e1",        # İnce gri kenarlık
        "border_highlight": "#2563eb",
        "accent_primary": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_soft": "#dbeafe",
        "text_main": "#0f172a",          # Koyu lacivert ana metin
        "text_muted": "#475569",         # Orta gri metin
        "text_subtle": "#94a3b8",
        "success": "#16a34a",
        "success_hover": "#15803d",
        "warning": "#d97706",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "info": "#0284c7",
        "badge_bg": "#f1f5f9",
        "input_bg": "#ffffff",
        "input_border": "#cbd5e1",
        "stepper_active": "#0284c7",
        "stepper_done": "#16a34a",
        "stepper_pending": "#94a3b8",
    },
}

# Geriye dönük uyumluluk için varsayılan PALETTE
PALETTE = THEMES["dark"]


def get_theme_palette(theme_name: str = "dark") -> Dict[str, str]:
    """Seçilen temanın renk sözlüğünü döndürür ('dark' veya 'light')."""
    return THEMES.get(theme_name.lower(), THEMES["dark"])


def get_speaker_color(speaker_name: str) -> Tuple[str, str]:
    """Konuşmacı adına göre tutarlı bir renk çifti (arka plan, yazı rengi) döndürür."""
    if speaker_name in SPEAKER_COLORS:
        return SPEAKER_COLORS[speaker_name]

    # Özel isimler ve bilinmeyen konuşmacılar için deterministik ve estetik renk paleti
    extended_palette = [
        ("#10b981", "#ffffff"),
        ("#8b5cf6", "#ffffff"),
        ("#f59e0b", "#ffffff"),
        ("#f43f5e", "#ffffff"),
        ("#06b6d4", "#ffffff"),
        ("#ec4899", "#ffffff"),
        ("#3b82f6", "#ffffff"),
        ("#84cc16", "#ffffff"),
        ("#14b8a6", "#ffffff"),
        ("#a855f7", "#ffffff"),
        ("#0284c7", "#ffffff"),
        ("#d97706", "#ffffff"),
    ]
    hash_val = int(hashlib.md5(speaker_name.encode("utf-8")).hexdigest(), 16)
    return extended_palette[hash_val % len(extended_palette)]
