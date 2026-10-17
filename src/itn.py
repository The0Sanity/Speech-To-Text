"""Türkçe Ters Metin Normalizasyonu (Inverse Text Normalization - ITN) ve Dolgu Sözcük Modülü.

Bu modül, konuşma tanıma (ASR) çıktısındaki sözlü ifadeleri standart yazılı biçime dönüştürür:
1. Türkçe sayı öbekleri ("iki bin yirmi altı" -> "2026")
2. Yüzde ifadeleri ("yüzde elli" -> "%50")
3. Para birimleri ("yüz lira" -> "100 TL", "elli dolar" -> "50 USD")
4. Sıra sayıları ("birinci" -> "1.", "ikinci" -> "2.")
5. Dolgu sözcük filtreleme ("ııı", "şey", "yani" vb.)
"""

import re
from typing import Dict, List, Optional, Tuple

# Sayı kelimeleri sözlüğü
_DIGITS: Dict[str, int] = {
    "sıfır": 0,
    "bir": 1,
    "iki": 2,
    "üç": 3,
    "dört": 4,
    "beş": 5,
    "altı": 6,
    "yedi": 7,
    "sekiz": 8,
    "dokuz": 9,
}

_TENS: Dict[str, int] = {
    "on": 10,
    "yirmi": 20,
    "otuz": 30,
    "kırk": 40,
    "elli": 50,
    "altmış": 60,
    "yetmiş": 70,
    "seksen": 80,
    "doksan": 90,
}

_SCALES: Dict[str, int] = {
    "yüz": 100,
    "bin": 1000,
    "milyon": 1000000,
    "milyar": 1000000000,
    "trilyon": 1000000000000,
}

_ORDINALS: Dict[str, int] = {
    "birinci": 1,
    "ikinci": 2,
    "üçüncü": 3,
    "dördüncü": 4,
    "beşinci": 5,
    "altıncı": 6,
    "yedinci": 7,
    "sekizinci": 8,
    "dokuzuncu": 9,
    "onuncu": 10,
    "yirminci": 20,
    "otuzuncu": 30,
    "kırkıncı": 40,
    "ellinci": 50,
    "altmışıncı": 60,
    "yetmişinci": 70,
    "sekseninci": 80,
    "doksanıncı": 90,
    "yüzüncü": 100,
    "bininci": 1000,
}

_CURRENCIES: Dict[str, str] = {
    "lira": "TL",
    "tl": "TL",
    "türk lirası": "TL",
    "dolar": "USD",
    "usd": "USD",
    "euro": "EUR",
    "avro": "EUR",
    "sterlin": "GBP",
}

# Dolgu sözcük kalıpları (yalnızca tam sözcük olarak eşleşir)
_DISFLUENCIES = [
    r"\bı+[ıhm]*\b",
    r"\be+[emh]*\b",
    r"\bhmm+\b",
    r"\bşey\b",
    r"\byani\b",
    r"\bımm+\b",
]


def words_to_number(words: List[str]) -> Optional[int]:
    """Bir dizi Türkçe sayı sözcüğünü tam sayıya çevirir.
    
    Örnek:
        ['iki', 'bin', 'yirmi', 'altı'] -> 2026
        ['yüz', 'yirmi', 'üç'] -> 123
        ['on', 'beş'] -> 15
    """
    if not words:
        return None

    total = 0
    current = 0

    for w in words:
        w_lower = w.lower()
        if w_lower in _DIGITS:
            val = _DIGITS[w_lower]
            current += val
        elif w_lower in _TENS:
            val = _TENS[w_lower]
            current += val
        elif w_lower == "yüz":
            if current == 0:
                current = 100
            else:
                current *= 100
        elif w_lower == "bin":
            if current == 0:
                current = 1000
            else:
                current *= 1000
            total += current
            current = 0
        elif w_lower in _SCALES:
            scale = _SCALES[w_lower]
            if current == 0:
                current = 1
            total += current * scale
            current = 0
        else:
            return None

    return total + current


def normalize_turkish_ordinals(text: str) -> str:
    """Türkçe sıra sayılarını dönüştürür ('birinci' -> '1.')."""
    def replace_ordinal(match: re.Match) -> str:
        word = match.group(0).lower()
        if word in _ORDINALS:
            return f"{_ORDINALS[word]}."
        return match.group(0)

    pattern = r"\b(" + "|".join(_ORDINALS.keys()) + r")\b"
    return re.sub(pattern, replace_ordinal, text, flags=re.IGNORECASE)


def normalize_turkish_percentages(text: str) -> str:
    """Türkçe yüzde ifadelerini dönüştürür ('yüzde elli' -> '%50')."""
    # "yüzde [sayı sözcükleri]" kalıbını ara
    all_num_words = list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys())
    num_word_pat = r"(?:" + "|".join(all_num_words) + r")"
    pattern = rf"\byüzde\s+({num_word_pat}(?:\s+{num_word_pat})*)\b"

    def replace_percent(match: re.Match) -> str:
        num_str = match.group(1).strip()
        num_words = num_str.split()
        val = words_to_number(num_words)
        if val is not None:
            return f"%{val}"
        return match.group(0)

    return re.sub(pattern, replace_percent, text, flags=re.IGNORECASE)


def normalize_turkish_currencies(text: str) -> str:
    """Para birimi sözcüklerini dönüştürür ('yüz lira' -> '100 TL', '50 dolar' -> '50 USD')."""
    all_num_words = list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys())
    num_word_pat = r"(?:" + "|".join(all_num_words) + r"|\d+)"
    curr_pat = r"(?:" + "|".join(re.escape(c) for c in _CURRENCIES.keys()) + r")"
    pattern = rf"\b({num_word_pat}(?:\s+{num_word_pat})*)\s+({curr_pat})\b"

    def replace_curr(match: re.Match) -> str:
        num_part = match.group(1).strip()
        curr_part = match.group(2).strip().lower()
        symbol = _CURRENCIES.get(curr_part, curr_part.upper())

        # Eğer sayı rakam ise
        if num_part.isdigit():
            return f"{num_part} {symbol}"
        
        # Sayı kelimeleri ise
        num_words = num_part.split()
        val = words_to_number(num_words)
        if val is not None:
            return f"{val} {symbol}"
        return match.group(0)

    return re.sub(pattern, replace_curr, text, flags=re.IGNORECASE)


def normalize_turkish_numbers(text: str) -> str:
    """Türkçe sayı sözcüklerini rakama dönüştürür ('iki bin yirmi altı' -> '2026')."""
    all_num_words = set(list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys()))
    words = text.split()
    if not words:
        return text

    result = []
    i = 0
    n = len(words)

    while i < n:
        raw_word = words[i]
        clean_word = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", raw_word).lower()

        # Sayı sözcüğü dizisi başlangıcı
        if clean_word in all_num_words:
            num_sequence = []
            punct_end = ""
            j = i

            while j < n:
                w_clean = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", words[j]).lower()
                if w_clean in all_num_words:
                    num_sequence.append(w_clean)
                    j += 1
                else:
                    break

            # Son kelimenin varsa noktalama işaretini sakla
            last_word = words[j - 1]
            punct_match = re.search(r"([^\wçğıöşüÇĞİÖŞÜ]+)$", last_word)
            if punct_match:
                punct_end = punct_match.group(1)

            parsed_num = words_to_number(num_sequence)
            if parsed_num is not None:
                result.append(f"{parsed_num}{punct_end}")
                i = j
                continue

        result.append(raw_word)
        i += 1

    return " ".join(result)


def remove_turkish_disfluencies(text: str) -> str:
    """Konuşmadaki duraklama ve dolgu sözcüklerini ('ııı', 'eee', 'şey', 'yani') temizler."""
    result = text
    for pat in _DISFLUENCIES:
        # Cümle başı veya ortasındaki dolguları temizle
        result = re.sub(pat, "", result, flags=re.IGNORECASE)

    # Fazla boşlukları ve çift noktalamaları toparla
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"\s+([,\.!?;:])", r"\1", result)
    return result.strip()


def apply_turkish_itn(
    text: str,
    convert_numbers: bool = True,
    convert_percentages: bool = True,
    convert_currencies: bool = True,
    convert_ordinals: bool = True,
    remove_fillers: bool = True,
) -> str:
    """Tüm Türkçe ters metin normalizasyonu (ITN) işlemlerini sırasıyla uygular."""
    if not text or not text.strip():
        return text

    result = text

    # 1. Dolgu sözcük temizliği
    if remove_fillers:
        result = remove_turkish_disfluencies(result)

    # 2. Yüzde ifadeleri (sayı dönüşümünden önce yapılmalı)
    if convert_percentages:
        result = normalize_turkish_percentages(result)

    # 3. Para birimleri (sayı dönüşümünden önce yapılmalı)
    if convert_currencies:
        result = normalize_turkish_currencies(result)

    # 4. Sıra sayıları
    if convert_ordinals:
        result = normalize_turkish_ordinals(result)

    # 5. Genel sayı dönüşümü
    if convert_numbers:
        result = normalize_turkish_numbers(result)

    return result
