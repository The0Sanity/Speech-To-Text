"""Unit tests for acoustic audio preprocessing in SesMetin Pro.

Validates Voice Activity Detection (VAD) energy gating, pre-emphasis filtering,
and peak loudness normalization.
"""

import unittest
import numpy as np
from src.transcription.audio_preprocessing import (
    apply_pre_emphasis,
    normalize_loudness,
    voice_activity_filter,
    preprocess_audio_pipeline
)


class TestAudioPreprocessing(unittest.TestCase):
    """Test suite for acoustic preprocessing routines."""

    def test_pre_emphasis_filter(self):
        """Verify pre-emphasis accentuates higher frequency components."""
        sr = 16000
        # Create a low-frequency tone plus silence
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = np.sin(2 * np.pi * 100 * t).astype(np.float32)
        filtered = apply_pre_emphasis(signal, coefficient=0.97)

        self.assertEqual(len(filtered), len(signal))
        self.assertTrue(np.all(np.isfinite(filtered)))
        # Pre-emphasis of constant signal should have minimal difference
        const_sig = np.ones(100, dtype=np.float32)
        const_filt = apply_pre_emphasis(const_sig, coefficient=0.97)
        self.assertAlmostEqual(float(const_filt[50]), 0.03, places=2)

    def test_normalize_loudness(self):
        """Verify loudness normalization scales signals to target peak safely."""
        low_signal = np.array([0.01, -0.02, 0.015, -0.01], dtype=np.float32)
        normalized = normalize_loudness(low_signal, target_peak=0.95)

        self.assertAlmostEqual(float(np.max(np.abs(normalized))), 0.95, places=2)

        # Silence should remain unchanged
        silent = np.zeros(100, dtype=np.float32)
        norm_silent = normalize_loudness(silent)
        self.assertTrue(np.all(norm_silent == 0))

    def test_voice_activity_filter(self):
        """Verify VAD trims leading and trailing silence."""
        sr = 16000
        silence = np.zeros(sr // 2, dtype=np.float32)
        tone = np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, sr // 2)).astype(np.float32) * 0.5
        padded = np.concatenate([silence, tone, silence])

        trimmed = voice_activity_filter(padded, sample_rate=sr, energy_threshold=0.01)
        self.assertLess(len(trimmed), len(padded))
        self.assertGreater(len(trimmed), 0)

    def test_pipeline_integration(self):
        """Verify the full end-to-end preprocessing pipeline."""
        sr = 16000
        signal = np.random.uniform(-0.3, 0.3, sr).astype(np.float32)
        processed = preprocess_audio_pipeline(signal, sample_rate=sr)

        self.assertIsInstance(processed, np.ndarray)
        self.assertEqual(processed.dtype, np.float32)
        self.assertTrue(np.max(np.abs(processed)) <= 1.0)


if __name__ == "__main__":
    unittest.main()
