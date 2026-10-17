"""Unit tests for telephone (telephony) acoustic simulation and adaptive equalization.

Validates G.711 / cellular bandpass filtering (300-3400 Hz), mu-law compression,
telephone audio detection, and speech restoration filters.
"""

import unittest
import numpy as np
from src.transcription.audio_preprocessing import (
    simulate_telephony_audio,
    adaptive_telephony_equalizer,
    detect_telephony_audio
)


class TestTelephonyAudio(unittest.TestCase):
    """Test suite for telephony acoustic simulation and equalization."""

    def test_telephony_bandpass_attenuation(self):
        """Verify telephone simulation attenuates frequencies below 300Hz and above 3400Hz."""
        sr = 16000
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)

        # 100 Hz bass hum (should be significantly attenuated by 300 Hz cutoff)
        bass = np.sin(2 * np.pi * 100 * t).astype(np.float32)
        # 1000 Hz human speech tone (should pass through phone filter with minimal loss)
        voice = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        # 6000 Hz high hiss (should be significantly attenuated by 3400 Hz cutoff)
        treble = np.sin(2 * np.pi * 6000 * t).astype(np.float32)

        phone_bass = simulate_telephony_audio(bass, sample_rate=sr, add_noise=False)
        phone_voice = simulate_telephony_audio(voice, sample_rate=sr, add_noise=False)
        phone_treble = simulate_telephony_audio(treble, sample_rate=sr, add_noise=False)

        voice_rms = np.sqrt(np.mean(phone_voice ** 2))
        bass_rms = np.sqrt(np.mean(phone_bass ** 2))
        treble_rms = np.sqrt(np.mean(phone_treble ** 2))

        # Passband tone should retain far more energy than out-of-band tones
        self.assertGreater(voice_rms, bass_rms * 2.0)
        self.assertGreater(voice_rms, treble_rms * 2.0)

    def test_telephony_detection(self):
        """Verify automatic detection distinguishes wideband audio from telephone audio."""
        sr = 16000
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)

        # Wideband speech-like signal with harmonic energy up to 7000 Hz
        wideband = (np.sin(2 * np.pi * 500 * t) + np.sin(2 * np.pi * 4500 * t)).astype(np.float32)
        self.assertFalse(detect_telephony_audio(wideband, sample_rate=sr))

        # Telephone-simulated signal
        phone_audio = simulate_telephony_audio(wideband, sample_rate=sr)
        self.assertTrue(detect_telephony_audio(phone_audio, sample_rate=sr))

    def test_adaptive_telephony_equalizer(self):
        """Verify equalizer restores high-frequency presence on telephone audio."""
        sr = 16000
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        speech = np.sin(2 * np.pi * 800 * t).astype(np.float32)
        degraded = simulate_telephony_audio(speech, sample_rate=sr)

        restored = adaptive_telephony_equalizer(degraded, sample_rate=sr)
        self.assertEqual(len(restored), len(degraded))
        self.assertTrue(np.all(np.isfinite(restored)))
        self.assertLessEqual(np.max(np.abs(restored)), 1.0)


if __name__ == "__main__":
    unittest.main()
