"""Windows 11 Fluent Design Flet tema renkleri, tipografi ve konuşmacı renk haritası."""

from typing import List

# Windows 11 Fluent Dark Renk Paleti
BG_APP = "#202020"
BG_CARD = "#2b2b2b"
BG_CARD_SECONDARY = "#242424"
BORDER_CARD = "#383838"

INPUT_BG = "#1c1c1c"
INPUT_BORDER = "#333333"

ACCENT_PRIMARY = "#0078d4"
ACCENT_HOVER = "#1084d8"
ACCENT_LIGHT = "#60cdff"

TEXT_MAIN = "#ffffff"
TEXT_MUTED = "#cccccc"
TEXT_SUBTLE = "#888888"

BTN_NEUTRAL = "#2d2d2d"
BTN_NEUTRAL_HOVER = "#383838"

DANGER = "#e11d48"
DANGER_HOVER = "#be123c"
SUCCESS = "#10b981"
WARNING = "#f59e0b"

# Geriye dönük uyumluluk ve genel tasarım takma adları (Aliases)
PRIMARY = ACCENT_PRIMARY
ACCENT = ACCENT_PRIMARY
BORDER_MUTED = BORDER_CARD
BORDER_SUBTLE = BORDER_CARD
STATUS_ERROR = DANGER
ERROR = DANGER

# Konuşmacı Ayrıştırma Renk Paleti
SPEAKER_COLORS: List[str] = [
    "#38bdf8",  # Açık Mavi
    "#34d399",  # Zümrüt Yeşili
    "#fbbf24",  # Amber Sarı
    "#f472b6",  # Pembe
    "#a78bfa",  # Mor
    "#fb923c",  # Turuncu
    "#4ade80",  # Açık Yeşil
    "#22d3ee",  # Camgöbeği
]


def get_speaker_color(speaker_id: str) -> str:
    """Konuşmacı kimliği için belirgin bir renk döndürür."""
    if not speaker_id:
        return SPEAKER_COLORS[0]

    # X1, X2, vb. formatından indeks çıkarma
    num_part = "".join(filter(str.isdigit, speaker_id))
    if num_part:
        idx = (int(num_part) - 1) % len(SPEAKER_COLORS)
        return SPEAKER_COLORS[idx]

    # İsim bazlı deterministik hash
    hash_val = sum(ord(c) for c in speaker_id)
    return SPEAKER_COLORS[hash_val % len(SPEAKER_COLORS)]
