"""Masaüstü arayüzü renk paletleri, temalar ve konuşmacı renk stilleri."""

import hashlib
from typing import Dict, Tuple

# Konuşmacı rozet renkleri (Arka plan, Yazı rengi)
SPEAKER_COLORS: Dict[str, Tuple[str, str]] = {
    "X1": ("#10b981", "#ffffff"),  # Zümrüt Yeşili
    "X2": ("#8b5cf6", "#ffffff"),  # Mor / Violet
    "X3": ("#f59e0b", "#ffffff"),  # Kehribar Sarısı
    "X4": ("#f43f5e", "#ffffff"),  # Gül Kurusu / Kırmızı
    "X5": ("#06b6d4", "#ffffff"),  # Camgöbeği (Cyan)
    "X6": ("#ec4899", "#ffffff"),  # Pembe
    "X7": ("#3b82f6", "#ffffff"),  # Mavi
    "X8": ("#84cc16", "#ffffff"),  # Limon Yeşili
}

PALETTE = {
    "bg_dark": "#12141a",
    "card_dark": "#1a1d26",
    "card_border_dark": "#2a2f3d",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "text_main": "#f3f4f6",
    "text_muted": "#9ca3af",
}


def get_speaker_color(speaker_name: str) -> Tuple[str, str]:
    """Konuşmacı adına göre tutarlı bir renk çifti döndürür."""
    if speaker_name in SPEAKER_COLORS:
        return SPEAKER_COLORS[speaker_name]

    # Bilinmeyen veya özel isim verilmiş konuşmacılar için deterministik renk üret
    palette_options = [
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
    ]
    hash_val = int(hashlib.md5(speaker_name.encode("utf-8")).hexdigest(), 16)
    return palette_options[hash_val % len(palette_options)]
