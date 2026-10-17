"""Faster-Whisper tabanlı Türkçe konuşma tanıma (Speech-To-Text) modülü."""

import os
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
    2. Zlib sıkıştırma oranı > 2.4 (tekrarlama döngüsü)
    """
    if no_speech_prob > 0.6 and avg_logprob < -1.0:
        return True
    if text and is_repetition_loop(text, threshold=threshold):
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


class WhisperTranscriber:
    """Faster-Whisper motorunu CPU üzerinde INT8 optimizasyonuyla çalıştıran sınıf."""

    def __init__(self, model_size: str = "small", cpu_threads: int = 4):
        """
        Args:
            model_size: Model boyutu ("tiny", "base", "small", "medium", "large-v3-turbo")
            cpu_threads: CPU çekirdek sayısı (i3-12100 için 4 önerilir)
        """
        self.model_size = model_size
        self.cpu_threads = cpu_threads
        self.download_root = str(MODELS_DIR)
        self.model: Optional[WhisperModel] = None

    def load_model(self, status_callback: Optional[Callable[[str], None]] = None) -> None:
        """Modeli önbellekten veya HuggingFace üzerinden yükler."""
        if self.model is None:
            if status_callback:
                status_callback(f"'{self.model_size}' modeli belleğe yükleniyor (CPU INT8)...")

            self.model = WhisperModel(
                model_size_or_path=self.model_size,
                device="cpu",
                compute_type="int8",
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
        beam_size: int = 5,
        vad_sensitivity: str = "high",
        apply_postprocessing: bool = True,
        apply_itn: bool = True,
        clean_disfluencies: bool = True,
        progress_callback: Optional[Callable[[float, str, Optional[Dict[str, Any]]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Verilen ses dosyasını metne dönüştürür.
        
        Args:
            audio_path: 16kHz WAV ses dosyasının yolu.
            language: Dil kodu (Varsayılan 'tr' - Türkçe).
            total_duration: Ses dosyasının toplam süresi (saniye cinsinden, ilerleme hesabı için).
            initial_prompt: Whisper modeline bağlam ve stil kazandırmak için başlangıç istemi.
            beam_size: Işın arama genişliği (varsayılan 5).
            vad_sensitivity: Ses aktivite tespiti hassasiyeti ('high' veya 'normal').
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

        # VAD (Ses Etkinliği Tespiti) Ayarları (Üretim standardı Silero VAD)
        vad_params = get_production_vad_parameters(sensitivity=vad_sensitivity)

        # Başlangıç istemi (Türkçe karakter ve noktalama doğruluğunu garantiler)
        prompt_to_use = initial_prompt
        if prompt_to_use is None and (language == "tr" or language == "auto"):
            prompt_to_use = DEFAULT_TURKISH_PROMPT

        # faster-whisper parametreleri:
        # beam_size=5 / best_of=5: Yüksek doğruluk
        # condition_on_previous_text=False: Halüsinasyon döngülerini ve sonsuz tekrarları engeller
        # repetition_penalty=1.15: Tekrarlayan kelimeleri cezalandırır
        # no_repeat_ngram_size=3: 3'lü sözcük tekrarını önler
        # temperature=[0.0, 0.2, 0.4, 0.6]: Hatalı çözümlerde alternatif sıcaklıkları dener
        segments_generator, info = self.model.transcribe(
            audio=audio_data,
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

        rolling_context = ""
        collected_segments: List[Dict[str, Any]] = []

        for seg_idx, segment in enumerate(segments_generator):
            text_cleaned = segment.text.strip()
            if not text_cleaned:
                continue

            avg_logprob = float(getattr(segment, "avg_logprob", 0.0) or 0.0)
            no_speech_prob = float(getattr(segment, "no_speech_prob", 0.0) or 0.0)
            comp_ratio = float(getattr(segment, "compression_ratio", 0.0) or calculate_compression_ratio(text_cleaned))

            # Güven ve tekrarlama filtreleme (Aşama 5)
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
            rolling_context = f"{rolling_context} {text_cleaned}".strip()

            # İlerleme hesabı (toplam ses süresine göre %15 ile %75 arası STT aşamasıdır)
            if audio_dur > 0 and progress_callback:
                progress_fraction = min(0.75, 0.15 + (segment.end / audio_dur) * 0.60)
                msg = f"Çözümleniyor: [{segment.end:.1f}s / {audio_dur:.1f}s] - \"{text_cleaned[:35]}...\""
                progress_callback(progress_fraction, msg, seg_dict)

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
