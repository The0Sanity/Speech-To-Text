"""Türkçe metin son-işleme modülü.

Whisper çıktısındaki yaygın hataları düzeltir:
- Tekrarlayan kelime/cümle temizliği
- Türkçe karakter düzeltmeleri
- Halüsinasyon tespiti ve kaldırma
- Gereksiz boşluk/noktalama temizliği
"""

import re
from typing import Any, Dict, List


# Whisper'ın Türkçe'de sıkça halüsinasyon gördüğü kalıplar
_HALLUCINATION_PATTERNS = [
    # Müzik/efekt etiketleri (Whisper bunları bazen tekrarlı ekler)
    r'(?i)\[müzik\]',
    r'(?i)\[music\]',
    r'(?i)\[alkış\]',
    r'(?i)\[applause\]',
    r'(?i)\[sessizlik\]',
    r'(?i)\[silence\]',
    # Abone ol / Like gibi YouTube overlay metinleri
    r'(?i)abone ol[un]*',
    r'(?i)subscribe',
    r'(?i)like buton',
    r'(?i)beğen buton',
    # Sadece noktalama / boşluk
    r'^[\s\.\,\!\?\;\:]+$',
]

# Whisper'ın Türkçe'de yaptığı yaygın karakter hataları
_CHAR_CORRECTIONS = {
    'İstanbul': 'İstanbul',  # placeholder - Whisper usually gets this right
    ' ,': ',',
    ' .': '.',
    ' !': '!',
    ' ?': '?',
    '  ': ' ',
}


def postprocess_segments(
    segments: List[Dict[str, Any]],
    remove_hallucinations: bool = True,
    remove_repeated_phrases: bool = True,
    min_segment_chars: int = 2,
) -> List[Dict[str, Any]]:
    """Tüm segmentlere Türkçe son-işleme uygular.
    
    Args:
        segments: Whisper segment listesi [{'id': ..., 'text': ..., 'start': ..., 'end': ...}]
        remove_hallucinations: Halüsinasyon kalıplarını kaldır
        remove_repeated_phrases: Tekrarlayan cümleleri kaldır
        min_segment_chars: Bu karakter sayısından kısa segmentleri kaldır
    
    Returns:
        Temizlenmiş segment listesi
    """
    cleaned = []
    prev_text = ""
    
    for seg in segments:
        text = seg.get("text", "").strip()
        
        if not text:
            continue
        
        # 1. Halüsinasyon kontrolü
        if remove_hallucinations and _is_hallucination(text):
            continue
        
        # 2. Tekrarlayan cümle kontrolü
        if remove_repeated_phrases:
            text = _remove_repeated_phrases(text)
        
        # 3. Türkçe karakter ve noktalama düzeltmeleri
        text = _fix_turkish_text(text)
        
        # 4. Minimum uzunluk kontrolü
        text_stripped = re.sub(r'[^\w]', '', text)
        if len(text_stripped) < min_segment_chars:
            continue
        
        # 5. Tamamen aynı ardışık segment tekrarı kontrolü
        normalized_curr = _normalize_for_comparison(text)
        normalized_prev = _normalize_for_comparison(prev_text)
        if normalized_curr == normalized_prev and normalized_curr:
            continue
        
        new_seg = seg.copy()
        new_seg["text"] = text
        cleaned.append(new_seg)
        prev_text = text
    
    # ID'leri yeniden numarala
    for i, seg in enumerate(cleaned):
        seg["id"] = i + 1
    
    return cleaned


def _is_hallucination(text: str) -> bool:
    """Metnin Whisper halüsinasyonu olup olmadığını kontrol eder."""
    for pattern in _HALLUCINATION_PATTERNS:
        if re.fullmatch(pattern, text.strip()):
            return True
    
    # Çok kısa ve sadece tekrar eden tek karakter/kelime
    words = text.strip().split()
    if len(words) >= 4:
        unique_words = set(w.lower() for w in words)
        if len(unique_words) == 1:
            return True  # Aynı kelime 4+ kez tekrar
    
    return False


def _remove_repeated_phrases(text: str) -> str:
    """Cümle içinde tekrarlanan sözcük gruplarını temizler.
    
    Örnek: 'merhaba merhaba nasılsın nasılsın' -> 'merhaba nasılsın'
    """
    # Remove consecutive duplicate words
    words = text.split()
    if len(words) <= 1:
        return text
    
    cleaned_words = [words[0]]
    for i in range(1, len(words)):
        if words[i].lower() != words[i-1].lower():
            cleaned_words.append(words[i])
    
    # Remove repeated 2-3 word phrases
    result = ' '.join(cleaned_words)
    for phrase_len in [3, 2]:
        result = _remove_repeated_ngrams(result, phrase_len)
    
    return result


def _remove_repeated_ngrams(text: str, n: int) -> str:
    """Tekrarlayan n-gram sözcük gruplarını kaldırır."""
    words = text.split()
    if len(words) < n * 2:
        return text
    
    i = 0
    result = []
    while i < len(words):
        if i + 2 * n <= len(words):
            phrase1 = ' '.join(words[i:i+n]).lower()
            phrase2 = ' '.join(words[i+n:i+2*n]).lower()
            if phrase1 == phrase2:
                result.extend(words[i:i+n])
                i += 2 * n
                # Skip further repeats of the same phrase
                while i + n <= len(words):
                    next_phrase = ' '.join(words[i:i+n]).lower()
                    if next_phrase == phrase1:
                        i += n
                    else:
                        break
                continue
        result.append(words[i])
        i += 1
    
    return ' '.join(result)


def _fix_turkish_text(text: str) -> str:
    """Türkçe metin düzeltmeleri uygular."""
    # Birden fazla boşluğu teke düşür
    text = re.sub(r' +', ' ', text)
    
    # Noktalama öncesi gereksiz boşlukları kaldır
    text = re.sub(r'\s+([,\.!?;:])', r'\1', text)
    
    # Cümle başı büyük harf (nokta/soru/ünlem sonrası)
    text = re.sub(r'([.!?])\s+([a-zçğıöşü])', 
                  lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
    
    # İlk karakter büyük harf
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    
    return text.strip()


def _normalize_for_comparison(text: str) -> str:
    """Karşılaştırma için metni normalleştirir (küçük harf, boşluk/noktalama kaldır)."""
    return re.sub(r'[^\wçğıöşüÇĞİÖŞÜ]', '', text.lower())
