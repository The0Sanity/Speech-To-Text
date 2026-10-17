"""Doğruluk iyileştirme modülleri için kapsamlı birim testleri.

Test Edilen Modüller:
1. src/audio_enhancer.py (Yüksek geçiren filtre, gürültü kapısı, normalizasyon)
2. src/text_postprocessor.py (Halüsinasyon temizliği, tekrar eden kelime/öbek kaldırma, Türkçe karakterler)
3. src/diarizer.py (Tek konuşmacı tespiti k=1)
4. src/transcriber.py (VAD hassasiyeti ve Türkçe başlangıç istemi)
"""

import os
import sys
import unittest
from pathlib import Path

# Proje dizinini ekle
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import soundfile as sf

from src.audio_enhancer import (
    apply_highpass_filter,
    apply_noise_gate,
    enhance_audio,
    normalize_audio,
    soft_clip,
)
from src.audio_processor import cleanup_temp_file
from src.diarizer import SpeakerDiarizer
from src.text_postprocessor import (
    _fix_turkish_text,
    _is_hallucination,
    _remove_repeated_phrases,
    postprocess_segments,
)
from src.transcriber import DEFAULT_TURKISH_PROMPT, WhisperTranscriber


class TestAccuracyEnhancements(unittest.TestCase):
    """Doğruluk ve iyileştirme test sınıfı."""

    @classmethod
    def setUpClass(cls):
        """Test ses verisi hazırla."""
        cls.test_dir = BASE_DIR / "temp" / "test_accuracy"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.sample_rate = 16000
        duration = 3.0

        t = np.linspace(0, duration, int(cls.sample_rate * duration), endpoint=False)
        # 50 Hz alçak frekans gürültüsü (hum) + 200 Hz konuşma tonu
        noise_50hz = 0.3 * np.sin(2 * np.pi * 50 * t)
        speech_200hz = 0.5 * np.sin(2 * np.pi * 200 * t)
        audio = noise_50hz + speech_200hz

        cls.raw_wav = str(cls.test_dir / "raw_noisy.wav")
        cls.enhanced_wav = str(cls.test_dir / "enhanced.wav")
        sf.write(cls.raw_wav, audio.astype(np.float32), cls.sample_rate)

    @classmethod
    def tearDownClass(cls):
        """Temizlik."""
        for p in [cls.raw_wav, cls.enhanced_wav]:
            if Path(p).exists():
                cleanup_temp_file(p)

    def test_01_highpass_filter(self):
        """80Hz yüksek geçiren filtrenin 50Hz gürültüsünü zayıflattığını doğrula."""
        t = np.linspace(0, 1.0, 16000, endpoint=False)
        sig_50hz = np.sin(2 * np.pi * 50 * t).astype(np.float32)
        filtered = apply_highpass_filter(sig_50hz, sample_rate=16000, cutoff_hz=80.0)

        orig_energy = np.mean(sig_50hz**2)
        filtered_energy = np.mean(filtered**2)
        self.assertLess(filtered_energy, orig_energy * 0.1)

    def test_02_normalize_and_soft_clip(self):
        """Normalizasyon ve yumuşak sınırlama testi."""
        data = np.array([0.1, -0.2, 0.4, -0.5], dtype=np.float32)
        norm = normalize_audio(data, target_db=-1.0)
        max_peak = np.max(np.abs(norm))
        # -1 dBFS ~= 0.891
        self.assertAlmostEqual(max_peak, 10 ** (-1.0 / 20.0), places=2)

        # Soft clipping test
        loud_data = np.array([0.5, 1.5, -2.0], dtype=np.float32)
        clipped = soft_clip(loud_data, threshold=0.95)
        self.assertLessEqual(np.max(np.abs(clipped)), 0.95)

    def test_03_noise_gate(self):
        """Gürültü kapısının sessiz bölümleri bastırdığını doğrula."""
        sample_rate = 16000
        # 1 saniye çok kısık gürültü (-50 dB)
        quiet_noise = (np.random.randn(sample_rate) * 0.001).astype(np.float32)
        gated = apply_noise_gate(quiet_noise, sample_rate, threshold_db=-40.0)
        self.assertLess(np.mean(gated**2), np.mean(quiet_noise**2))

    def test_04_enhance_audio_pipeline(self):
        """Uçtan uca ses iyileştirme testi."""
        out = enhance_audio(self.raw_wav, self.enhanced_wav)
        self.assertTrue(os.path.isfile(out))
        info = sf.info(out)
        self.assertEqual(info.samplerate, self.sample_rate)
        self.assertEqual(info.channels, 1)

    def test_05_hallucination_detection(self):
        """Whisper halüsinasyon kalıplarının tespiti."""
        self.assertTrue(_is_hallucination("[MÜZİK]"))
        self.assertTrue(_is_hallucination("[Music]"))
        self.assertTrue(_is_hallucination("[alkış]"))
        self.assertTrue(_is_hallucination("abone olun"))
        self.assertTrue(_is_hallucination("Abone Olun"))
        self.assertTrue(_is_hallucination("merhaba merhaba merhaba merhaba"))
        self.assertFalse(_is_hallucination("Bugün Valorant maçına başladık."))

    def test_06_repeated_phrases_removal(self):
        """Tekrarlayan kelime ve n-gram öbeklerinin temizlenmesi."""
        text1 = "merhaba merhaba nasılsın nasılsın"
        cleaned1 = _remove_repeated_phrases(text1)
        self.assertEqual(cleaned1, "merhaba nasılsın")

        text2 = "bu bir denemedir bu bir denemedir çok güzel"
        cleaned2 = _remove_repeated_phrases(text2)
        self.assertEqual(cleaned2, "bu bir denemedir çok güzel")

    def test_07_turkish_text_fixing(self):
        """Türkçe noktalama ve boşluk düzeltmeleri."""
        raw = "merhaba   dünya . nasılsın ?"
        fixed = _fix_turkish_text(raw)
        self.assertEqual(fixed, "Merhaba dünya. Nasılsın?")

    def test_08_postprocess_segments(self):
        """Segment listesi üzerinde filtreleme testi."""
        segments = [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "[MÜZİK]"},
            {"id": 2, "start": 1.0, "end": 2.5, "text": "oyun başladı oyun başladı"},
            {"id": 3, "start": 2.5, "end": 3.0, "text": "..."},
            {"id": 4, "start": 3.0, "end": 4.5, "text": "silahı aldım ."},
        ]
        processed = postprocess_segments(segments)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]["text"], "Oyun başladı")
        self.assertEqual(processed[1]["text"], "Silahı aldım.")
        self.assertEqual(processed[0]["id"], 1)
        self.assertEqual(processed[1]["id"], 2)

    def test_09_single_speaker_detection(self):
        """Tek bir konuşmacının (monolog) k=1 olarak doğru ayrıştırılması."""
        speech_segments = [
            {"start": 0.5, "end": 1.5, "text": "Birinci cümle."},
            {"start": 1.8, "end": 2.8, "text": "İkinci cümle."},
        ]
        diarizer = SpeakerDiarizer(speaker_prefix="X")
        # Açıkça 1 konuşmacı verildiğinde k=1 kalmalı
        res1 = diarizer.diarize(
            audio_path=self.raw_wav,
            speech_segments=speech_segments,
            num_speakers=1,
        )
        self.assertTrue(all(d["speaker"] == "X1" for d in res1))

    def test_10_transcriber_prompt_and_vad_defaults(self):
        """WhisperTranscriber başlangıç istemi ve VAD ayarları testi."""
        self.assertIn("Türkçe", DEFAULT_TURKISH_PROMPT)
        self.assertIn("ç, ğ, ı, ö, ş, ü", DEFAULT_TURKISH_PROMPT)
        transcriber = WhisperTranscriber(model_size="small")
        self.assertEqual(transcriber.model_size, "small")


if __name__ == "__main__":
    unittest.main()
