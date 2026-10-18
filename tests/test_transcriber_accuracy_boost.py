"""Unit tests for ASR accuracy boosting: hotwords, domain prompts, and acoustic filtering."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.transcriber import WhisperTranscriber, build_domain_hotwords
from src.audio_processor import apply_acoustic_music_filter


class TestTranscriberAccuracyBoost(unittest.TestCase):
    """Test suite for ASR accuracy boosting features."""

    def test_build_domain_hotwords_default(self):
        """Test default Turkish domain hotwords generation."""
        hotwords = build_domain_hotwords()
        self.assertIsInstance(hotwords, str)
        self.assertIn("patates", hotwords.lower())
        self.assertIn("domates", hotwords.lower())
        self.assertIn("şarkı", hotwords.lower())

    def test_build_domain_hotwords_with_custom(self):
        """Test merging custom terms with domain hotwords."""
        custom_terms = "Yapay Zeka, CTranslate2, Whisper"
        hotwords = build_domain_hotwords(custom_terms=custom_terms)
        self.assertIn("yapay zeka", hotwords.lower())
        self.assertIn("patates", hotwords.lower())

    def test_apply_acoustic_music_filter(self):
        """Test acoustic bandpass / high-pass filtering on audio signals."""
        import numpy as np
        sr = 16000
        # Create a synthetic signal with DC offset and 30Hz bass rumble
        t = np.linspace(0, 1.0, sr, endpoint=False)
        rumble = 0.5 * np.sin(2 * np.pi * 30 * t) + 0.2  # 30Hz low freq rumble + DC
        speech_freq = 0.4 * np.sin(2 * np.pi * 1000 * t)  # 1kHz speech freq
        composite = rumble + speech_freq

        filtered = apply_acoustic_music_filter(composite, sample_rate=sr, cutoff_hz=80.0)
        self.assertEqual(len(filtered), len(composite))
        # Mean (DC offset) and low frequency rumble energy should be significantly reduced
        self.assertLess(abs(float(np.mean(filtered))), 0.05)


if __name__ == "__main__":
    unittest.main()
