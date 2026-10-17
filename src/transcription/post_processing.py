"""Turkish Inverse Text Normalization (ITN) and Phonetic Correction module for SesMetin Pro.

Converts spoken Turkish numbers, percentages, currencies, dates, and common phonetic
transcription confusions into standard, highly accurate written Turkish.
"""

import re
from typing import Dict, List, Optional, Tuple

# Spoken number dictionaries
_DIGITS: Dict[str, int] = {
    "sıfır": 0, "sifir": 0,
    "bir": 1,
    "iki": 2,
    "üç": 3, "uc": 3,
    "dört": 4, "dort": 4,
    "beş": 5, "bes": 5,
    "altı": 6, "alti": 6,
    "yedi": 7,
    "sekiz": 8,
    "dokuz": 9,
}

_TENS: Dict[str, int] = {
    "on": 10,
    "yirmi": 20,
    "otuz": 30,
    "kırk": 40, "kirk": 40,
    "elli": 50,
    "altmış": 60, "altmis": 60,
    "yetmiş": 70, "yetmis": 70,
    "seksen": 80,
    "doksan": 90,
}

_SCALES: Dict[str, int] = {
    "yüz": 100, "yuz": 100,
    "bin": 1000,
    "milyon": 1000000,
    "milyar": 1000000000,
    "trilyon": 1000000000000,
}

_ORDINALS: Dict[str, int] = {
    "birinci": 1, "ikinci": 2, "üçüncü": 3, "ucuncu": 3,
    "dördüncü": 4, "dorduncu": 4, "beşinci": 5, "besinci": 5,
    "altıncı": 6, "altinci": 6, "yedinci": 7, "sekizinci": 8,
    "dokuzuncu": 9, "onuncu": 10, "yirminci": 20, "otuzuncu": 30,
    "kırkıncı": 40, "kirkinci": 40, "ellinci": 50, "yüzüncü": 100,
}

_CURRENCIES: Dict[str, str] = {
    "lira": "TL",
    "türk lirası": "TL", "turk lirasi": "TL",
    "tl": "TL",
    "dolar": "USD",
    "usd": "USD",
    "euro": "EUR", "avro": "EUR",
    "sterlin": "GBP",
}

_COMMON_IDIOMS: List[str] = [
    "üç beş kişi", "uc bes kisi",
    "üç beş", "uc bes",
    "bir iki",
    "dört bir yan", "dort bir yan",
]

_PHONETIC_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bses\s+metin\s+pro\b", re.IGNORECASE), "SesMetin Pro"),
    (re.compile(r"\bses\s+metin\b", re.IGNORECASE), "SesMetin"),
    (re.compile(r"\bsesmetin\b", re.IGNORECASE), "SesMetin"),
    (re.compile(r"\byapa\s+zeka\b", re.IGNORECASE), "yapay zeka"),
    (re.compile(r"\bderin\s+o[gğ]renme\b", re.IGNORECASE), "derin öğrenme"),
    (re.compile(r"\bkonu[sş]ma\s+tan[iı]ma\b", re.IGNORECASE), "konuşma tanıma"),
    (re.compile(r"\bmakine\s+o[gğ]renmesi\b", re.IGNORECASE), "makine öğrenmesi"),
    (re.compile(r"\byapay\s+zeka\s+modeli\b", re.IGNORECASE), "yapay zeka modeli"),
    (re.compile(r"\btesk\b", re.IGNORECASE), "test"),
]


def format_thousands(num: int) -> str:
    """Format an integer with Turkish dot thousands separator (e.g. 100000 -> 100.000)."""
    return f"{num:,}".replace(",", ".")


def parse_turkish_number_words(words: List[str]) -> Optional[int]:
    """Parse a list of Turkish number words into an integer."""
    if not words:
        return None

    total = 0
    current = 0

    for w in words:
        w_low = w.lower()
        if w_low in _DIGITS:
            current += _DIGITS[w_low]
        elif w_low in _TENS:
            current += _TENS[w_low]
        elif w_low in ("yüz", "yuz"):
            if current == 0:
                current = 100
            else:
                current *= 100
        elif w_low == "bin":
            if current == 0:
                current = 1000
            else:
                current *= 1000
            total += current
            current = 0
        elif w_low in _SCALES:
            scale = _SCALES[w_low]
            if current == 0:
                current = 1
            total += current * scale
            current = 0
        else:
            return None

    return total + current


class TurkishITNProcessor:
    """Inverse Text Normalization processor for Turkish language."""

    @staticmethod
    def normalize_percentages(text: str) -> str:
        """Convert spoken percentages to standard symbols ('yüzde elli' -> '%50', 'yüzde sıfır nokta bir' -> '%0.1')."""
        # Decimal percentages: "yüzde sıfır nokta bir" / "yuzde sifir nokta bir"
        decimal_pat = r"\b(?:yüzde|yuzde)\s+(?:sıfır|sifir)\s+(?:nokta|virgül|virgul)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\b"
        def repl_dec(m: re.Match) -> str:
            dec_word = m.group(1).lower()
            if dec_word in _DIGITS:
                return f"%0.{_DIGITS[dec_word]}"
            return m.group(0)

        text = re.sub(decimal_pat, repl_dec, text, flags=re.IGNORECASE)

        # Standard integer percentages
        all_words = list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys())
        word_pat = r"(?:" + "|".join(all_words) + r")"
        pat = rf"\b(?:yüzde|yuzde)\s+({word_pat}(?:\s+{word_pat})*)\b"

        def repl_pct(m: re.Match) -> str:
            words = m.group(1).strip().split()
            val = parse_turkish_number_words(words)
            if val is not None:
                return f"%{val}"
            return m.group(0)

        return re.sub(pat, repl_pct, text, flags=re.IGNORECASE)

    @staticmethod
    def normalize_currencies(text: str) -> str:
        """Convert spoken currencies to standard format ('kırk beş lira' -> '45 TL')."""
        all_words = list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys())
        word_pat = r"(?:" + "|".join(all_words) + r"|\d+)"
        curr_pat = r"(?:" + "|".join(re.escape(k) for k in _CURRENCIES.keys()) + r")"
        pat = rf"\b({word_pat}(?:\s+{word_pat})*)\s+({curr_pat})\b"

        def repl_curr(m: re.Match) -> str:
            num_part = m.group(1).strip()
            curr_part = m.group(2).strip().lower()
            symbol = _CURRENCIES.get(curr_part, curr_part.upper())

            if num_part.isdigit():
                formatted_num = format_thousands(int(num_part)) if int(num_part) >= 1000 else num_part
                return f"{formatted_num} {symbol}"

            num_words = num_part.split()
            val = parse_turkish_number_words(num_words)
            if val is not None:
                formatted_val = format_thousands(val) if val >= 1000 else str(val)
                return f"{formatted_val} {symbol}"
            return m.group(0)

        return re.sub(pat, repl_curr, text, flags=re.IGNORECASE)

    @staticmethod
    def normalize_numbers(text: str) -> str:
        """Convert spoken number word sequences to numeric digits with Turkish thousands separator."""
        # Decimal numbers like "sıfır nokta bir" -> "0.1"
        text = re.sub(
            r"\b(?:sıfır|sifir)\s+(?:nokta|virgül|virgul)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\b",
            lambda m: f"0.{_DIGITS[m.group(1).lower()]}" if m.group(1).lower() in _DIGITS else m.group(0),
            text,
            flags=re.IGNORECASE
        )

        all_words = set(list(_DIGITS.keys()) + list(_TENS.keys()) + list(_SCALES.keys()))
        words = text.split()
        if not words:
            return text

        result = []
        i = 0
        n = len(words)

        while i < n:
            raw_word = words[i]
            clean_word = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", raw_word).lower()

            if clean_word in all_words:
                num_seq = []
                punct_end = ""
                j = i

                while j < n:
                    w_clean = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", words[j]).lower()
                    if w_clean in all_words:
                        num_seq.append(w_clean)
                        j += 1
                    else:
                        break

                last_word = words[j - 1]
                punct_match = re.search(r"([^\wçğıöşüÇĞİÖŞÜ]+)$", last_word)
                if punct_match:
                    punct_end = punct_match.group(1)

                parsed_num = parse_turkish_number_words(num_seq)
                if parsed_num is not None:
                    if parsed_num >= 1000:
                        formatted = format_thousands(parsed_num)
                    else:
                        formatted = str(parsed_num)
                    result.append(f"{formatted}{punct_end}")
                    i = j
                    continue

            result.append(raw_word)
            i += 1

        return " ".join(result)


class TurkishPhoneticCorrector:
    """Corrects frequent acoustic and phonetic speech recognition confusions in Turkish."""

    @staticmethod
    def correct_phonetic_confusions(text: str) -> str:
        """Apply targeted phonetic regex substitutions to fix acoustic errors."""
        res = text
        for pat, replacement in _PHONETIC_REPLACEMENTS:
            res = pat.sub(replacement, res)
        return res


def post_process_transcript(
    text: str,
    apply_itn: bool = True,
    apply_phonetic: bool = True
) -> str:
    """Full-pipeline post-processor for Turkish speech transcripts.

    Args:
        text: Raw transcription string.
        apply_itn: Enable Inverse Text Normalization (numbers, %, currency).
        apply_phonetic: Enable phonetic and domain confusion corrections.

    Returns:
        Refined and normalized transcript string.
    """
    if not text or not text.strip():
        return text

    res = text.strip()

    # 1. Protect common idioms from being broken up into numbers
    idiom_placeholders = {}
    for idx, idiom in enumerate(_COMMON_IDIOMS):
        token = f"__IDIOM_PLACEHOLDER_{idx}__"
        pattern = re.compile(rf"\b{re.escape(idiom)}\b", re.IGNORECASE)
        if pattern.search(res):
            idiom_placeholders[token] = "üç beş kişi" if "kişi" in idiom or "kisi" in idiom else idiom
            res = pattern.sub(token, res)

    # 2. Phonetic corrections
    if apply_phonetic:
        res = TurkishPhoneticCorrector.correct_phonetic_confusions(res)

    # 3. ITN: Percentages
    if apply_itn:
        res = TurkishITNProcessor.normalize_percentages(res)

    # 4. ITN: Currencies
    if apply_itn:
        res = TurkishITNProcessor.normalize_currencies(res)

    # 5. ITN: General numbers
    if apply_itn:
        res = TurkishITNProcessor.normalize_numbers(res)

    # 6. Restore preserved idioms
    for token, idiom_val in idiom_placeholders.items():
        res = res.replace(token, idiom_val)

    # 7. Clean up whitespace and punctuation
    res = re.sub(r"\s+", " ", res)
    res = re.sub(r"\s+([,\.!?;:])", r"\1", res)

    return res.strip()
