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
    apply_itn: bool = True,
    clean_disfluencies: bool = True,
    min_segment_chars: int = 2,
) -> List[Dict[str, Any]]:
    """Tüm segmentlere Türkçe son-işleme uygular.
    
    Args:
        segments: Whisper segment listesi [{'id': ..., 'text': ..., 'start': ..., 'end': ...}]
        remove_hallucinations: Halüsinasyon kalıplarını kaldır
        remove_repeated_phrases: Tekrarlayan cümleleri kaldır
        apply_itn: Türkçe sayı, yüzde ve para birimlerini yazılı biçime dönüştür (ITN)
        clean_disfluencies: Dolgu sözcükleri ('ııı', 'şey' vb.) temizle
        min_segment_chars: Bu karakter sayısından kısa segmentleri kaldır
    
    Returns:
        Temizlenmiş segment listesi
    """
    from src.itn import apply_turkish_itn

    cleaned = []
    prev_text = ""
    consecutive_identical_seg_count = 1
    
    for seg in segments:
        text = seg.get("text", "").strip()
        
        if not text:
            continue
        
        # 1. Halüsinasyon kontrolü
        if remove_hallucinations and _is_hallucination(text):
            continue
        
        # 2. Tekrarlayan cümle kontrolü (Türkçe ikilemeleri korur)
        if remove_repeated_phrases:
            text = _remove_repeated_phrases(text)
        
        # 3. Türkçe karakter ve noktalama düzeltmeleri
        text = _fix_turkish_text(text)
        
        # 4. Türkçe Ters Metin Normalizasyonu (ITN) ve Dolgu Temizliği
        if apply_itn or clean_disfluencies:
            text = apply_turkish_itn(
                text,
                convert_numbers=apply_itn,
                convert_percentages=apply_itn,
                convert_currencies=apply_itn,
                convert_ordinals=apply_itn,
                remove_fillers=clean_disfluencies,
            )
            from src.transcription.post_processing import post_process_transcript
            text = post_process_transcript(text, apply_itn=apply_itn, apply_phonetic=True)
        
        # 5. Minimum uzunluk kontrolü
        text_stripped = re.sub(r'[^\w]', '', text)
        if len(text_stripped) < min_segment_chars:
            continue
        
        # 6. Ardışık segment tekrarı kontrolü (Şarkılarda nakarat tekrarlarını 2 sefere kadar korur)
        normalized_curr = _normalize_for_comparison(text)
        normalized_prev = _normalize_for_comparison(prev_text)
        if normalized_curr == normalized_prev and normalized_curr:
            consecutive_identical_seg_count += 1
            if consecutive_identical_seg_count > 2:
                continue
        else:
            consecutive_identical_seg_count = 1
        
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
    
    stripped = text.strip()
    # Sadece semboller ve boşluklardan ibaretse
    letters = re.sub(r'[^\w]', '', stripped)
    if not letters:
        return True
    
    # Sadece tek bir harfin 6+ kez tekrarlanması (örn. 'a a a a a a')
    unique_letters = set(letters.lower())
    if len(letters) >= 6 and len(unique_letters) == 1:
        return True
    
    return False


def _remove_repeated_phrases(text: str) -> str:
    """Cümle içinde tekrarlanan sözcük gruplarını temizlerken Türkçe ikilemeleri korur.
    
    Örnek:
    - 'pisi pisi' -> 'pisi pisi' (ikileme korunur)
    - 'kuçu kuçu kuçu kuçu' -> 'kuçu kuçu' (maksimum 2 tekrara sınırlandırılır)
    """
    words = text.split()
    if len(words) <= 1:
        return text
    
    def norm(w: str) -> str:
        return re.sub(r'[^\w]', '', w.lower())

    cleaned_words = [words[0]]
    consecutive_count = 1
    
    for i in range(1, len(words)):
        w_curr = norm(words[i])
        w_prev = norm(words[i - 1])
        if w_curr == w_prev and w_curr:
            consecutive_count += 1
            # Türkçe ikilemeler (pisi pisi, adım adım, yavaş yavaş) için en fazla 2 tekrara izin ver
            if consecutive_count <= 2:
                cleaned_words.append(words[i])
        else:
            consecutive_count = 1
            cleaned_words.append(words[i])
    
    # Çoklu sözcük grupları tekrarı (2 ve 3 sözcüklü kalıplar)
    result = ' '.join(cleaned_words)
    for phrase_len in [3, 2]:
        result = _remove_repeated_ngrams(result, phrase_len)
    
    return result


def _remove_repeated_ngrams(text: str, n: int) -> str:
    """Tekrarlayan n-gram sözcük gruplarını en fazla 2 tekrara kadar tutarak temizler."""
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
                # En fazla 2 kez tekrara izin ver (örn. nakarat: 'domates domates')
                result.extend(words[i:i+2*n])
                i += 2 * n
                # 3. ve sonraki sonsuz döngü tekrarlarını atla
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
