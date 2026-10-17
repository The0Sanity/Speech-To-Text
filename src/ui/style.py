"""Masaüstü ve dizüstü sistemler için Windows 11 Fluent Design renk paletleri, tipografi ve stiller."""

import hashlib
from typing import Dict, Tuple

# Windows 11 Fluent Tipografi Ailesi
FONT_FAMILY = "Segoe UI Variable Text"
FONT_FALLBACK = "Segoe UI"

# Konuşmacı rozet renkleri (Arka plan rengi, Yazı rengi)
SPEAKER_COLORS: Dict[str, Tuple[str, str]] = {
    "X1": ("#0078d4", "#ffffff"),  # Windows Mavi
    "X2": ("#744da9", "#ffffff"),  # Fluent Mor
    "X3": ("#d97706", "#ffffff"),  # Kehribar Sarısı
    "X4": ("#e11d48", "#ffffff"),  # Gül Kurusu
    "X5": ("#0284c7", "#ffffff"),  # Gök Mavisi
    "X6": ("#c026d3", "#ffffff"),  # Fuşya
    "X7": ("#2563eb", "#ffffff"),  # Safir Mavisi
    "X8": ("#16a34a", "#ffffff"),  # Yeşil
    "X9": ("#0d9488", "#ffffff"),  # Turkuaz
    "X10": ("#9333ea", "#ffffff"), # Lavanta
    "X11": ("#ca8a04", "#ffffff"), # Altın
    "X12": ("#4f46e5", "#ffffff"), # İndigo
}

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        # Windows 11 Fluent Dark (Mica / Acrylic)
        "bg_app": "#202020",             # Windows 11 Fluent Dark Ana Zemin
        "bg_main": "#202020",            # Eşdeğer ana zemin
        "bg_card": "#2b2b2b",            # Yükseltilmiş kart yüzeyi
        "bg_card_secondary": "#323232",  # İkincil kart yüzeyi
        "bg_card_hover": "#383838",      # Kart hover
        "border_card": "#383838",        # İnce Fluent kenarlık (1px)
        "border_highlight": "#0078d4",   # Odaklanmış kenarlık (Fluent Accent)
        "accent_primary": "#0078d4",     # Windows 11 Fluent Birincil Vurgu
        "accent_hover": "#1084d9",       # Vurgu hover
        "accent_soft": "#1a365d",        # Yumuşak vurgu
        "text_main": "#ffffff",          # Beyaz ana metin
        "text_primary": "#ffffff",
        "text_muted": "#a6a6a6",         # Gri ikincil metin
        "text_subtle": "#767676",        # Soluk metin
        "btn_neutral": "#2e2e2e",        # Nötr Fluent buton yüzeyi
        "btn_neutral_hover": "#3a3a3a",  # Nötr buton hover
        "btn_neutral_border": "#3c3c3c", # Nötr buton kenarlık
        "success": "#0078d4",            # Ana aksiyon butonu (Windows Fluent Blue)
        "success_hover": "#1084d9",
        "warning": "#d97706",
        "danger": "#e11d48",
        "danger_hover": "#be123c",
        "info": "#0284c7",
        "badge_bg": "#2b2b2b",
        "input_bg": "#1c1c1c",           # Girdi alanı (bir kademe daha koyu iç boşluk)
        "input_border": "#3c3c3c",
        "stepper_active": "#60cdff",     # Windows 11 Aydınlık Mavi
        "stepper_done": "#0078d4",       # Tamamlanan adım
        "stepper_pending": "#484848",    # Bekleyen adım
    },
    "light": {
        # Windows 11 Fluent Light
        "bg_app": "#f3f3f3",             # Windows 11 Fluent Light Ana Zemin
        "bg_main": "#f3f3f3",
        "bg_card": "#ffffff",            # Beyaz kart yüzeyi
        "bg_card_secondary": "#f9f9f9",  # İkincil yüzey
        "bg_card_hover": "#f0f0f0",
        "border_card": "#e5e5e5",        # İnce gri kenarlık
        "border_highlight": "#0078d4",
        "accent_primary": "#0078d4",
        "accent_hover": "#1084d9",
        "accent_soft": "#e0eefe",
        "text_main": "#1c1c1c",          # Koyu ana metin
        "text_primary": "#1c1c1c",
        "text_muted": "#5c5c5c",         # Orta gri metin
        "text_subtle": "#8a8a8a",
        "btn_neutral": "#fbfbfb",
        "btn_neutral_hover": "#f0f0f0",
        "btn_neutral_border": "#d1d1d1",
        "success": "#0078d4",
        "success_hover": "#1084d9",
        "warning": "#b45309",
        "danger": "#e11d48",
        "danger_hover": "#be123c",
        "info": "#0284c7",
        "badge_bg": "#f9f9f9",
        "input_bg": "#ffffff",
        "input_border": "#d1d1d1",
        "stepper_active": "#0078d4",
        "stepper_done": "#1084d9",
        "stepper_pending": "#cccccc",
    },
}

THEME_PALETTES = THEMES
PALETTE = THEMES["dark"]


def get_theme_palette(theme_name: str = "dark") -> Dict[str, str]:
    """Seçilen temanın renk sözlüğünü döndürür ('dark' veya 'light')."""
    return THEMES.get(theme_name.lower(), THEMES["dark"])


def get_speaker_color(speaker_name: str) -> Tuple[str, str]:
    """Konuşmacı adına göre tutarlı bir renk çifti (arka plan, yazı rengi) döndürür."""
    if speaker_name in SPEAKER_COLORS:
        return SPEAKER_COLORS[speaker_name]

    extended_palette = [
        ("#0078d4", "#ffffff"),
        ("#744da9", "#ffffff"),
        ("#d97706", "#ffffff"),
        ("#e11d48", "#ffffff"),
        ("#0284c7", "#ffffff"),
        ("#c026d3", "#ffffff"),
        ("#2563eb", "#ffffff"),
        ("#16a34a", "#ffffff"),
        ("#0d9488", "#ffffff"),
        ("#9333ea", "#ffffff"),
    ]
    hash_val = int(hashlib.md5(speaker_name.encode("utf-8")).hexdigest(), 16)
    return extended_palette[hash_val % len(extended_palette)]
