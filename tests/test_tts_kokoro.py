"""Kokoro-82M yerel konuşma sentezleyici (TTS) ve veri üretim testleri."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.tts.kokoro_engine import KokoroSynthesizer, SyntheticAudioSample


class TestKokoroSynthesizer(unittest.TestCase):
    """Kokoro-82M konuşma sentezleyici ve sentetik veri üretimi testleri."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.synthesizer = KokoroSynthesizer(output_dir=Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_available_voices(self):
        """Mevcut konuşmacı seslerinin listelendiğini doğrula."""
        voices = self.synthesizer.get_available_voices()
        self.assertIsInstance(voices, list)
        self.assertGreaterEqual(len(voices), 2)
        # En az bir kadın ve bir erkek sesi olmalı
        voice_ids = [v["id"] for v in voices]
        self.assertTrue(any(v.startswith("af_") for v in voice_ids))
        self.assertTrue(any(v.startswith("am_") for v in voice_ids))

    def test_02_synthetic_sample_generation(self):
        """Sentetik ses örneği üretiminin WAV dosyası ve meta veri döndürdüğünü doğrula."""
        text = "SesMetin Pro ile Türkçe konuşma tanıma modeli eğitimi."
        sample = self.synthesizer.synthesize_sample(
            text=text,
            voice="af_bella",
            speed=1.0,
            sample_rate=16000,
        )
        self.assertIsInstance(sample, SyntheticAudioSample)
        self.assertEqual(sample.text, text)
        self.assertTrue(os.path.exists(sample.audio_path))
        self.assertGreater(sample.duration_seconds, 0.0)
        self.assertEqual(sample.sample_rate, 16000)

    def test_03_speed_augmentation(self):
        """Hız parametresi değiştirildiğinde ses süresinin değiştiğini doğrula."""
        text = "Hızlı ve yavaş okuma testi."
        slow_sample = self.synthesizer.synthesize_sample(text=text, voice="am_adam", speed=0.8)
        fast_sample = self.synthesizer.synthesize_sample(text=text, voice="am_adam", speed=1.2)

        self.assertGreater(slow_sample.duration_seconds, fast_sample.duration_seconds)

    def test_04_save_dataset_metadata(self):
        """Sentetik veri setinin JSONL olarak doğru kaydedildiğini doğrula."""
        samples = [
            SyntheticAudioSample(
                audio_path="test1.wav",
                text="İlk cümle.",
                duration_seconds=1.5,
                voice="af_bella",
                speed=1.0,
                sample_rate=16000,
            ),
            SyntheticAudioSample(
                audio_path="test2.wav",
                text="İkinci cümle.",
                duration_seconds=2.0,
                voice="am_adam",
                speed=1.1,
                sample_rate=16000,
            ),
        ]
        meta_file = Path(self.temp_dir) / "metadata.jsonl"
        self.synthesizer.save_dataset_manifest(samples, meta_file)

        self.assertTrue(meta_file.exists())
        lines = meta_file.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("İlk cümle.", lines[0])


if __name__ == "__main__":
    unittest.main()
