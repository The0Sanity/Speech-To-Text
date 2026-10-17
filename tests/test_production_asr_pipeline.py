"""Production ASR Enhancement Pipeline birim testleri.

6 Aşamalı Üretim Standardı:
1. Ses Sinyali Standartlaştırma (EBU R128 + Bandpass)
2. Nöral VAD Parametreleri & Dolgu
3. Konuşmacı Ayrıştırma & Kelime Hizalama Entegrasyonu
4. Alan Bağlamı & Hareketli İstem (Rolling Context Prompt)
5. Güven Filtreleme & Zlib Sıkıştırma Oranı Halüsinasyon Tespiti
6. Deterministik Türkçe Ters Metin Normalizasyonu (ITN) & Dolgu Sözcük Temizliği
"""

import unittest
from unittest.mock import MagicMock, patch

from src.audio_enhancer import apply_bandpass_filter
from src.audio_processor import build_ffmpeg_filter_string
from src.itn import (
    apply_turkish_itn,
    normalize_turkish_currencies,
    normalize_turkish_numbers,
    normalize_turkish_ordinals,
    normalize_turkish_percentages,
    remove_turkish_disfluencies,
)
from src.transcriber import (
    build_rolling_prompt,
    calculate_compression_ratio,
    get_production_vad_parameters,
    is_repetition_loop,
    should_filter_segment,
)


class TestProductionAudioProcessing(unittest.TestCase):
    """Aşama 1: Ses ön-işleme ve FFmpeg filtre testleri."""

    def test_ffmpeg_filter_string_full(self):
        """EBU R128 ve bant geçiren filtre komutunun doğru oluşturulduğunu doğrular."""
        filter_str = build_ffmpeg_filter_string(
            enable_loudnorm=True,
            highpass_hz=80,
            lowpass_hz=7600,
            target_lufs=-16.0,
            target_tp=-1.5,
            target_lra=11.0,
        )
        self.assertIn("highpass=f=80", filter_str)
        self.assertIn("lowpass=f=7600", filter_str)
        self.assertIn("loudnorm=I=-16:TP=-1.5:LRA=11", filter_str)

    def test_ffmpeg_filter_string_disabled_loudnorm(self):
        """Loudnorm kapalıyken sadece bant geçiren filtrelerin eklendiğini doğrular."""
        filter_str = build_ffmpeg_filter_string(
            enable_loudnorm=False,
            highpass_hz=80,
            lowpass_hz=7600,
        )
        self.assertIn("highpass=f=80", filter_str)
        self.assertIn("lowpass=f=7600", filter_str)
        self.assertNotIn("loudnorm", filter_str)

    def test_apply_bandpass_filter_shape_and_dtype(self):
        """Scipy tabanlı bant geçiren filtrenin veri şeklini ve tipini koruduğunu doğrular."""
        import numpy as np
        sr = 16000
        t = np.linspace(0, 1, sr, endpoint=False)
        # 50 Hz (rumble) + 1000 Hz (speech) + 8000 Hz (high hiss)
        sig = np.sin(2 * np.pi * 50 * t) + np.sin(2 * np.pi * 1000 * t) + np.sin(2 * np.pi * 8000 * t)
        filtered = apply_bandpass_filter(sig.astype(np.float32), sr, low_cutoff=80.0, high_cutoff=7600.0)
        self.assertEqual(filtered.shape, sig.shape)
        self.assertEqual(filtered.dtype, np.float32)


class TestProductionVAD(unittest.TestCase):
    """Aşama 2: Silero Nöral VAD parametre testleri."""

    def test_production_vad_parameters_high_sensitivity(self):
        """High sensitivity modunda 400-600ms sessizlik ve 200-300ms tampon doğrulaması."""
        params = get_production_vad_parameters(sensitivity="high")
        self.assertIn("threshold", params)
        self.assertGreaterEqual(params["speech_pad_ms"], 200)
        self.assertLessEqual(params["speech_pad_ms"], 300)
        self.assertGreaterEqual(params["min_silence_duration_ms"], 400)
        self.assertLessEqual(params["min_silence_duration_ms"], 600)

    def test_production_vad_parameters_normal_sensitivity(self):
        """Normal modda standart VAD eşiklerinin korunduğunu doğrular."""
        params = get_production_vad_parameters(sensitivity="normal")
        self.assertGreaterEqual(params["threshold"], 0.45)
        self.assertGreaterEqual(params["speech_pad_ms"], 200)


class TestDomainContextAndRollingPrompt(unittest.TestCase):
    """Aşama 4: Alan bağlamı ve hareketli istem (Rolling Context Prompt) testleri."""

    def test_build_rolling_prompt_empty_history(self):
        """Geçmiş olmadan başlangıç sözlüğünün aynen döndüğünü doğrular."""
        glossary = "Supabase, TEKNOFEST, Next.js"
        prompt = build_rolling_prompt(base_prompt=glossary, previous_text="")
        self.assertEqual(prompt, glossary)

    def test_build_rolling_prompt_appends_last_150_chars(self):
        """Son 150 karakterin bağlama eklendiğini doğrular."""
        glossary = "Terimler: Supabase, Python."
        long_prev = "Bu konuşma çok uzun bir önceki konuşmanın içeriğidir. " * 5
        prompt = build_rolling_prompt(base_prompt=glossary, previous_text=long_prev, max_context_chars=150)
        self.assertTrue(prompt.startswith(glossary))
        # Eklenen bağlam 150 karakteri aşmamalı
        appended_context = prompt[len(glossary):].strip()
        self.assertLessEqual(len(appended_context), 150)
        self.assertTrue(long_prev.strip().endswith(appended_context))


class TestConfidenceAndRepetitionDetection(unittest.TestCase):
    """Aşama 5: Güven filtreleme ve zlib sıkıştırma oranı testleri."""

    def test_compression_ratio_calculation(self):
        """Zlib sıkıştırma oranının hesaplandığını doğrular."""
        text = "Normal bir Türkçe cümle örneğidir bu."
        ratio = calculate_compression_ratio(text)
        self.assertIsInstance(ratio, float)
        self.assertGreater(ratio, 0.0)

    def test_is_repetition_loop_detection(self):
        """Halüsinasyon döngülerinin (>2.4 sıkıştırma oranı) yakalandığını doğrular."""
        repetition = "evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet evet"
        normal_text = "Bugün toplantıda yeni nesil ASR boru hattı mimarisini tartıştık ve önemli kararlar aldık."
        self.assertTrue(is_repetition_loop(repetition, threshold=2.4))
        self.assertFalse(is_repetition_loop(normal_text, threshold=2.4))

    def test_should_filter_segment(self):
        """Düşük güvenli sessizlik veya tekrarlama döngüsü olan segmentlerin elendiğini doğrular."""
        # 1. no_speech > 0.6 AND avg_logprob < -1.0 -> Elenmeli
        self.assertTrue(should_filter_segment(avg_logprob=-1.2, no_speech_prob=0.75, text="fısıltı"))
        # 2. Yüksek güvenli normal konuşma -> Korunmalı
        self.assertFalse(should_filter_segment(avg_logprob=-0.25, no_speech_prob=0.05, text="Anlaşılır konuşma."))
        # 3. Yüksek tekrarlama döngüsü -> Elenmeli
        loop_text = "ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve ve"
        self.assertTrue(should_filter_segment(avg_logprob=-0.1, no_speech_prob=0.01, text=loop_text))


class TestTurkishInverseTextNormalization(unittest.TestCase):
    """Aşama 6: Türkçe ITN ve dolgu sözcük filtre testleri."""

    def test_normalize_turkish_numbers_basic(self):
        """Temel sayıların rakama dönüştürülmesini test eder."""
        self.assertEqual(normalize_turkish_numbers("bir"), "1")
        self.assertEqual(normalize_turkish_numbers("on beş"), "15")
        self.assertEqual(normalize_turkish_numbers("yüz yirmi üç"), "123")
        self.assertEqual(normalize_turkish_numbers("iki bin yirmi altı"), "2026")
        self.assertEqual(normalize_turkish_numbers("beş yüz kırk iki"), "542")

    def test_normalize_turkish_ordinals(self):
        """Sıra sayılarını test eder."""
        self.assertEqual(normalize_turkish_ordinals("birinci"), "1.")
        self.assertEqual(normalize_turkish_ordinals("ikinci"), "2.")
        self.assertEqual(normalize_turkish_ordinals("onuncu"), "10.")

    def test_normalize_turkish_percentages(self):
        """Yüzde ifadelerini test eder."""
        self.assertEqual(normalize_turkish_percentages("yüzde elli"), "%50")
        self.assertEqual(normalize_turkish_percentages("yüzde yirmi beş"), "%25")
        self.assertEqual(normalize_turkish_percentages("yüzde yüz"), "%100")

    def test_normalize_turkish_currencies(self):
        """Para birimi ifadelerini test eder."""
        self.assertEqual(normalize_turkish_currencies("yüz lira"), "100 TL")
        self.assertEqual(normalize_turkish_currencies("elli dolar"), "50 USD")
        self.assertEqual(normalize_turkish_currencies("yirmi euro"), "20 EUR")

    def test_remove_turkish_disfluencies(self):
        """Dolgu seslerin ('ııı', 'eee', vb.) temizlenmesini ve anlamlı sözcüklerin ('şey', 'yani') korunmasını test eder."""
        raw = "Ben ııı bugün eee projeyi hmmm tamamladım."
        cleaned = remove_turkish_disfluencies(raw)
        self.assertEqual(cleaned, "Ben bugün projeyi tamamladım.")

        # Anlamlı sözcüklerin korunduğunu doğrula
        text_with_valid_words = "En önemli şey sağlıktır yani bu böyledir."
        cleaned_valid = remove_turkish_disfluencies(text_with_valid_words)
        self.assertIn("şey", cleaned_valid)
        self.assertIn("yani", cleaned_valid)

    def test_apply_turkish_itn_integrated(self):
        """Tüm ITN kurallarının birleşik metin üzerindeki etkisini test eder."""
        text = "Toplantı iki bin yirmi altı yılında yüzde elli katılım ile yapıldı."
        result = apply_turkish_itn(text, convert_numbers=True, convert_percentages=True, remove_fillers=True)
        self.assertIn("2026", result)
        self.assertIn("%50", result)


if __name__ == "__main__":
    unittest.main()
