"""Faster-Whisper tabanlı Türkçe konuşma tanıma (Speech-To-Text) modülü."""

import os
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from faster_whisper import WhisperModel
from src.config import MODELS_DIR


DEFAULT_TURKISH_PROMPT = (
    "Merhaba, bu kayıt Türkçe konuşma içermektedir. "
    "Lütfen noktalama işaretlerine, Türkçe karakterlere (ç, ğ, ı, ö, ş, ü) ve cümle akışına dikkat ediniz."
)


def get_production_vad_parameters(sensitivity: str = "high") -> Dict[str, Any]:
    """Silero VAD için üretim düzeyinde akıllı semantik bölme parametreleri.
    
    Özellikler:
    - 400ms-600ms sessizlik aralığı (kelimeleri ortadan bölmeyi engeller)
    - 200ms-300ms sınır dolgusu (baş/son ünsüzlerin ve eklerin kırpılmasını önler)
    """
    if sensitivity == "high":
        return {
            "threshold": 0.35,
            "min_speech_duration_ms": 150,
            "max_speech_duration_s": float("inf"),
            "min_silence_duration_ms": 450,
            "speech_pad_ms": 250,
        }
    return {
        "threshold": 0.50,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": float("inf"),
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 200,
    }


def get_adaptive_vad_parameters(sensitivity: str = "high", is_music: bool = False) -> Dict[str, Any]:
    """Müzikli parçalar ve şarkılar için adaptif VAD parametreleri üretir."""
    if is_music:
        return {
            "threshold": 0.15,
            "min_speech_duration_ms": 100,
            "max_speech_duration_s": float("inf"),
            "min_silence_duration_ms": 600,
            "speech_pad_ms": 300,
        }
    return get_production_vad_parameters(sensitivity=sensitivity)


def clean_trailing_repetitions(text: str, max_repeats: int = 2) -> str:
    """Metin sonundaki tekrarlayan n-gram halüsinasyon döngülerini temizler.
    
    Örnek:
    'Bir patates ... sekiz patates sekiz patates sekiz patates sekiz patates'
    -> 'Bir patates ... sekiz patates sekiz patates'
    """
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= 2:
        return text.strip()

    import re
    def norm(w: str) -> str:
        return re.sub(r'[^\w]', '', w.lower())

    norm_words = [norm(w) for w in words]

    # n-gram boyutunu 4'ten 1'e kadar dene
    for k in (4, 3, 2, 1):
        if len(norm_words) < k * 2:
            continue
        unit = norm_words[-k:]
        if not any(unit):
            continue
        
        repeats = 1
        pos = len(norm_words) - k
        while pos >= k:
            prev_block = norm_words[pos - k : pos]
            if prev_block == unit:
                repeats += 1
                pos -= k
            else:
                break
        
        if repeats > max_repeats:
            keep_count = len(words) - (repeats - max_repeats) * k
            words = words[:keep_count]
            norm_words = norm_words[:keep_count]

    return " ".join(words).strip()


def calculate_compression_ratio(text: str) -> float:
    """Metnin zlib sıkıştırma oranını hesaplar.
    
    Tekrarlayan halüsinasyon döngüleri (örn. 'evet evet evet...') yüksek orana sahiptir (>2.4).
    """
    raw_bytes = text.strip().encode("utf-8")
    if not raw_bytes:
        return 0.0
    compressed = zlib.compress(raw_bytes)
    return round(len(raw_bytes) / max(1, len(compressed)), 3)


def is_repetition_loop(text: str, threshold: float = 2.4, min_len: int = 25) -> bool:
    """Metnin halüsinasyon/tekrarlama döngüsüne girip girmediğini kontrol eder."""
    stripped = text.strip()
    if len(stripped) < min_len:
        return False
    return calculate_compression_ratio(stripped) > threshold


def should_filter_segment(
    avg_logprob: float,
    no_speech_prob: float,
    text: str = "",
    threshold: float = 2.4,
) -> bool:
    """Güvenilirlik ve halüsinasyon filtre kriterlerini denetler.
    
    Kriterler:
    1. no_speech_prob > 0.6 VE avg_logprob < -1.0 (hayalet fısıltı / sessizlik gürültüsü)
    2. Tamamen anlamsız kısa karakter döngüleri (örn. '. . . . . .')
    """
    if no_speech_prob > 0.6 and avg_logprob < -1.0:
        return True
    
    stripped = text.strip() if text else ""
    if not stripped:
        return True
        
    import re
    cleaned_chars = [c for c in stripped if c.isalnum()]
    if not cleaned_chars:
        return True
    if len(cleaned_chars) >= 10 and len(set(cleaned_chars)) == 1:
        return True

    words = stripped.split()
    if len(words) >= 6 and len(set(re.sub(r'[^\w]', '', w.lower()) for w in words)) == 1:
        return True

    return False


def build_rolling_prompt(base_prompt: str, previous_text: str, max_context_chars: int = 150) -> str:
    """Önceki parçanın son 150 karakterini başlangıç istemine ekleyerek bağlam sürekliliği sağlar."""
    base = (base_prompt or "").strip()
    prev = (previous_text or "").strip()
    if not prev:
        return base
    rolling_part = prev[-max_context_chars:].strip()
    if not base:
        return rolling_part
    return f"{base} {rolling_part}"


TURKISH_COMMON_DOMAIN_HOTWORDS = [
    "patates", "domates", "portakal", "şarkı", "maymuncuk",
    "pisi", "kuçu", "düt", "mama", "hapşu", "mini", "kuş", "tavşan", "fare", "inek", "köpek", "kedi",
    "merhaba", "günaydın", "teşekkürler", "evet", "hayır", "tamam",
]

def build_domain_hotwords(custom_terms: Optional[str] = None) -> str:
    """ASR tanıma doğruluğunu artırmak için Türkçe etki alanı anahtar sözcüklerini (hotwords) oluşturur."""
    words = list(TURKISH_COMMON_DOMAIN_HOTWORDS)
    if custom_terms:
        import re
        tokens = [w.strip() for w in re.split(r"[,;\n]+", custom_terms) if w.strip()]
        for tok in tokens:
            if tok not in words:
                words.append(tok)
    return " ".join(words)


class WhisperTranscriber:
    """Faster-Whisper motorunu CPU veya CUDA üzerinde çalıştıran sınıf."""

    def __init__(
        self,
        model_size: str = "small",
        cpu_threads: int = 4,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        """
        Args:
            model_size: Model boyutu ("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo")
            cpu_threads: CPU çekirdek sayısı
            device: Çalışma cihazı ("cpu" veya "cuda")
            compute_type: Sayısal hassasiyet ("int8", "float16", "float32")
        """
        self.model_size = model_size
        self.cpu_threads = cpu_threads
        self.device = device or "cpu"
        self.compute_type = compute_type or "int8"
        self.download_root = str(MODELS_DIR)
        self.model: Optional[WhisperModel] = None

    def load_model(self, status_callback: Optional[Callable[[str], None]] = None) -> None:
        """Modeli önbellekten veya HuggingFace üzerinden yükler."""
        if self.model is None:
            if status_callback:
                status_callback(f"'{self.model_size}' modeli belleğe yükleniyor ({self.device.upper()} {self.compute_type})...")

            model_path = self.model_size
            try:
                from src.models.catalog import get_model_spec
                spec = get_model_spec(self.model_size)
                if spec:
                    local_dir = Path(self.download_root) / self.model_size
                    if local_dir.exists() and (local_dir / "model.bin").exists():
                        model_path = str(local_dir)
                    elif spec.repo_id:
                        model_path = spec.repo_id
            except Exception:
                pass

            self.model = WhisperModel(
                model_size_or_path=model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                download_root=self.download_root,
            )

            if status_callback:
                status_callback(f"'{self.model_size}' modeli hazır.")

    def transcribe(
        self,
        audio_path: str,
        language: str = "tr",
        total_duration: float = 0.0,
        initial_prompt: Optional[str] = None,
        hotwords: Optional[str] = None,
        beam_size: int = 5,
        vad_sensitivity: str = "high",
        vocal_isolation: bool = True,
        apply_postprocessing: bool = True,
        apply_itn: bool = True,
        clean_disfluencies: bool = True,
        progress_callback: Optional[Callable[[float, str, Optional[Dict[str, Any]]], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> List[Dict[str, Any]]:
        """
        Verilen ses dosyasını metne dönüştürür.
        
        Args:
            audio_path: 16kHz WAV ses dosyasının yolu.
            language: Dil kodu (Varsayılan 'tr' - Türkçe).
            total_duration: Ses dosyasının toplam süresi (saniye cinsinden, ilerleme hesabı için).
            initial_prompt: Whisper modeline bağlam ve stil kazandırmak için başlangıç istemi.
            hotwords: ASR çözücüye önceliklendirilecek anahtar kelimeler / ipuçları.
            beam_size: Işın arama genişliği (varsayılan 5).
            vad_sensitivity: Ses aktivite tespiti hassasiyeti ('high' veya 'normal').
            vocal_isolation: Müzikli veya ritimli seslerde vokal ayrıştırma uygular.
            apply_postprocessing: Çıktıda Türkçe metin temizleme ve halüsinasyon filtresi.
            progress_callback: İlerleme fonksiyonu (yüzde, durum mesajı, son segment).
            
        Returns:
            Segment listesi: [{'id': int, 'start': float, 'end': float, 'text': str, ...}]
        """
        self.load_model(status_callback=lambda msg: progress_callback(0.05, msg, None) if progress_callback else None)

        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")

        # Sesi soundfile ile oku ve numpy float32 formatında Whisper'a ilet
        import numpy as np
        import soundfile as sf

        audio_data, sr = sf.read(audio_path, dtype="float32")
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        if progress_callback:
            progress_callback(0.10, "Gelişmiş Türkçe konuşma tanıma başlatılıyor...", None)

        start_time = time.time()
        rms = float(np.sqrt(np.mean(audio_data ** 2))) if len(audio_data) > 0 else 0.0

        # İsteğe bağlı adaptif vokal ayrıştırma filtresi (HPSS)
        audio_to_transcribe = audio_data
        if vocal_isolation:
            try:
                from src.audio_processor import apply_hpss_vocal_filter
                audio_to_transcribe = apply_hpss_vocal_filter(audio_data, sample_rate=16000, bypass_if_clean=True)
            except Exception:
                audio_to_transcribe = audio_data

        # VAD (Ses Etkinliği Tespiti) Ayarları (Üretim standardı Silero VAD)
        vad_params = get_production_vad_parameters(sensitivity=vad_sensitivity)

        # Başlangıç istemi ve Hotword çözümü
        prompt_to_use = initial_prompt
        if prompt_to_use is None and (language == "tr" or language == "auto"):
            if "tiny" in self.model_size or "base" in self.model_size:
                prompt_to_use = None
            else:
                prompt_to_use = DEFAULT_TURKISH_PROMPT

        hotwords_to_use = hotwords
        if hotwords_to_use is None and (language == "tr" or language == "auto"):
            hotwords_to_use = build_domain_hotwords()

        # faster-whisper parametreleri:
        # beam_size=5 / best_of=5: Yüksek doğruluk
        # condition_on_previous_text=False: Halüsinasyon döngülerini ve sonraki pencerelere sızmasını engeller
        # repetition_penalty=1.15: Tekrarlayan kelimeleri cezalandırır
        # no_repeat_ngram_size=3: 3'lü sözcük tekrarını önler
        # temperature=[0.0, 0.2, 0.4, 0.6]: Hatalı çözümlerde alternatif sıcaklıkları dener
        # hotwords: Türkçe alan sözlüğü ile sözcük doğruluğunu en üst düzeye çıkarır
        segments_generator, info = self.model.transcribe(
            audio=audio_to_transcribe,
            language=language if language != "auto" else None,
            task="transcribe",
            beam_size=beam_size,
            best_of=beam_size,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=vad_params,
            initial_prompt=prompt_to_use,
            condition_on_previous_text=False,
            repetition_penalty=1.15,
            no_repeat_ngram_size=3,
            temperature=[0.0, 0.2, 0.4, 0.6],
            hotwords=hotwords_to_use,
        )

        detected_lang = info.language
        lang_prob = info.language_probability
        audio_dur = total_duration or info.duration or 1.0

        if progress_callback:
            progress_callback(
                0.15,
                f"Dil doğrulandı: {detected_lang.upper()} (%{int(lang_prob * 100)}) - Çözümleme yapılıyor...",
                None,
            )

        collected_segments: List[Dict[str, Any]] = []

        for seg_idx, segment in enumerate(segments_generator):
            if cancel_event and cancel_event.is_set():
                break

            text_cleaned = clean_trailing_repetitions(segment.text.strip())
            if not text_cleaned:
                continue

            avg_logprob = float(getattr(segment, "avg_logprob", 0.0) or 0.0)
            no_speech_prob = float(getattr(segment, "no_speech_prob", 0.0) or 0.0)
            comp_ratio = float(getattr(segment, "compression_ratio", 0.0) or calculate_compression_ratio(text_cleaned))

            # Güven ve tekrarlama filtreleme
            if should_filter_segment(avg_logprob, no_speech_prob, text=text_cleaned):
                continue

            words_data = []
            if segment.words:
                for w in segment.words:
                    words_data.append({
                        "word": w.word,
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2),
                    })

            seg_dict = {
                "id": len(collected_segments) + 1,
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text_cleaned,
                "words": words_data,
                "avg_logprob": round(avg_logprob, 3),
                "no_speech_prob": round(no_speech_prob, 3),
                "compression_ratio": round(comp_ratio, 3),
            }
            collected_segments.append(seg_dict)

            # İlerleme hesabı
            if audio_dur > 0 and progress_callback:
                progress_fraction = min(0.75, 0.15 + (segment.end / audio_dur) * 0.60)
                msg = f"Çözümleniyor: [{segment.end:.1f}s / {audio_dur:.1f}s] - \"{text_cleaned[:35]}...\""
                progress_callback(progress_fraction, msg, seg_dict)

        # VAD müzik/ritim nedeniyle konuşmayı yutmuşsa ve ses enerjisi varsa doğrudan çözümleme kurtarması
        total_decoded_duration = sum(s["end"] - s["start"] for s in collected_segments) if collected_segments else 0.0
        vad_dropped_speech = (len(collected_segments) == 0) or (audio_dur >= 10.0 and total_decoded_duration < 0.35 * audio_dur)
        if vad_dropped_speech and rms > 0.015 and not (cancel_event and cancel_event.is_set()):
            if progress_callback:
                progress_callback(0.20, "Müzikli ses tespit edildi, HPSS vokal ayrıştırma ve doğrudan çözümleme moduna geçiliyor...", None)
            
            from src.audio_processor import apply_hpss_vocal_filter
            filtered_fallback_audio = apply_hpss_vocal_filter(audio_data, sample_rate=16000)

            fallback_gen, _ = self.model.transcribe(
                audio=filtered_fallback_audio,
                language=language if language != "auto" else None,
                task="transcribe",
                beam_size=beam_size,
                best_of=beam_size,
                word_timestamps=True,
                vad_filter=False,
                initial_prompt=prompt_to_use,
                condition_on_previous_text=False,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3,
                temperature=[0.0, 0.2, 0.4, 0.6],
                hotwords=hotwords_to_use,
            )
            fallback_segments: List[Dict[str, Any]] = []
            for seg in fallback_gen:
                if cancel_event and cancel_event.is_set():
                    break
                t_clean = clean_trailing_repetitions(seg.text.strip())
                if not t_clean:
                    continue
                avg_lp = float(getattr(seg, "avg_logprob", 0.0) or 0.0)
                nsp = float(getattr(seg, "no_speech_prob", 0.0) or 0.0)
                c_ratio = float(getattr(seg, "compression_ratio", 0.0) or calculate_compression_ratio(t_clean))
                if should_filter_segment(avg_lp, nsp, text=t_clean):
                    continue
                w_data = []
                if seg.words:
                    for w in seg.words:
                        w_data.append({
                            "word": w.word,
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                            "probability": round(w.probability, 2),
                        })
                s_dict = {
                    "id": len(fallback_segments) + 1,
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": t_clean,
                    "words": w_data,
                    "avg_logprob": round(avg_lp, 3),
                    "no_speech_prob": round(nsp, 3),
                    "compression_ratio": round(c_ratio, 3),
                }
                fallback_segments.append(s_dict)
                if audio_dur > 0 and progress_callback:
                    p_frac = min(0.75, 0.20 + (seg.end / audio_dur) * 0.55)
            total_fallback_dur = sum(s["end"] - s["start"] for s in fallback_segments)
            if total_fallback_dur > total_decoded_duration or len(fallback_segments) > len(collected_segments):
                collected_segments = fallback_segments

        # TDK Dil Modeli ve Fonetik Sözlük Düzeltmesi (Türkçe için)
        if (language in ("tr", "auto")) and collected_segments:
            try:
                from src.language_model import TDKLanguageModelRescorer
                rescorer = TDKLanguageModelRescorer()
                for seg in collected_segments:
                    if seg.get("text"):
                        seg["text"] = rescorer.snap_sentence(seg["text"])
            except Exception:
                pass

        # Çıktıya Türkçe son-işleme uygula (halüsinasyonları, ITN ve dolgu sözcükleri temizler)
        if apply_postprocessing and collected_segments:
            from src.text_postprocessor import postprocess_segments
            collected_segments = postprocess_segments(
                collected_segments,
                apply_itn=apply_itn,
                clean_disfluencies=clean_disfluencies,
            )

        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(
                0.75,
                f"Konuşma tanıma tamamlandı ({len(collected_segments)} segment, {elapsed:.1f} sn).",
                None,
            )

        return collected_segments
