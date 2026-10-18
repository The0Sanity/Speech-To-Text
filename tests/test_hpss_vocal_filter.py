"""Unit tests for Harmonic/Percussive Sound Separation (HPSS) vocal pre-filtering."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
from src.audio_processor import apply_hpss_vocal_filter


class TestHPSSVocalFilter(unittest.TestCase):
    """Test suite for harmonic/percussive speech vocal filtering."""

    def setUp(self):
        self.sample_rate = 16000
        duration = 1.0  # 1 second
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)

        # 1. Harmonic speech-like fundamental frequency (220 Hz pitch + harmonics)
        self.harmonic_vocal = (
            0.5 * np.sin(2 * np.pi * 220 * t)
            + 0.3 * np.sin(2 * np.pi * 440 * t)
            + 0.15 * np.sin(2 * np.pi * 880 * t)
        ).astype(np.float32)

        # 2. Percussive sharp transient pulses (drum beat click track)
        self.percussive_noise = np.zeros_like(t)
        pulse_indices = np.arange(0, len(t), int(self.sample_rate * 0.25))
        for idx in pulse_indices:
            self.percussive_noise[idx : idx + 20] = 0.8

        self.mixed_audio = self.harmonic_vocal + self.percussive_noise

    def test_01_hpss_filter_suppresses_percussive_transients(self):
        """HPSS filtering should isolate vocal harmonics and attenuate sharp clicks."""
        filtered = apply_hpss_vocal_filter(self.mixed_audio, sample_rate=self.sample_rate)

        self.assertEqual(len(filtered), len(self.mixed_audio))
        # Peak transient in mixed audio was >= 1.3
        self.assertLess(np.max(np.abs(filtered)), np.max(np.abs(self.mixed_audio)))
        # Energy should be preserved close to pure harmonic vocal
        vocal_energy = np.mean(self.harmonic_vocal ** 2)
        filtered_energy = np.mean(filtered ** 2)
        self.assertAlmostEqual(filtered_energy, vocal_energy, delta=vocal_energy * 0.5)

    def test_02_hpss_clean_audio_adaptive_bypass(self):
        """Pure harmonic speech with no percussion should be preserved without degradation."""
        filtered = apply_hpss_vocal_filter(
            self.harmonic_vocal,
            sample_rate=self.sample_rate,
            bypass_if_clean=True,
        )
        # Should be almost identical to original vocal signal
        diff = np.max(np.abs(filtered - self.harmonic_vocal))
        self.assertLess(diff, 0.05)

    def test_03_zero_and_silence_handling(self):
        """Silence or zero-array audio should not raise division by zero or errors."""
        silence = np.zeros(self.sample_rate, dtype=np.float32)
        filtered = apply_hpss_vocal_filter(silence, sample_rate=self.sample_rate)
        self.assertEqual(len(filtered), len(silence))
        self.assertTrue(np.all(filtered == 0))


if __name__ == "__main__":
    unittest.main()
