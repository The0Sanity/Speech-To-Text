"""Unit tests for long-form (5 to 10 minute) audio segmentation and rolling context.

Validates semantic VAD chunking at natural speech pauses, rolling context prompt
management, and accurate timestamp alignment across 300-600 second audio streams.
"""

import unittest
import numpy as np
from src.transcription.engine import LongFormAudioProcessor


class TestLongFormProcessor(unittest.TestCase):
    """Test suite for long-form audio processing."""

    def setUp(self):
        self.processor = LongFormAudioProcessor(chunk_target_sec=30.0, max_context_chars=120)

    def test_semantic_chunking_on_simulated_longform(self):
        """Verify 5-minute (300s) audio with pauses is split at silence intervals."""
        sr = 16000
        total_duration = 300.0  # 5 minutes
        num_samples = int(sr * total_duration)

        # Create audio with alternating speech (20s) and silence (2s)
        audio = np.zeros(num_samples, dtype=np.float32)
        cycle_sec = 22.0
        for start_sec in np.arange(0, total_duration, cycle_sec):
            end_sec = min(total_duration, start_sec + 20.0)
            s_idx = int(start_sec * sr)
            e_idx = int(end_sec * sr)
            t = np.linspace(start_sec, end_sec, e_idx - s_idx, endpoint=False)
            audio[s_idx:e_idx] = 0.4 * np.sin(2 * np.pi * 300 * t).astype(np.float32)

        chunks = self.processor.split_longform_audio(audio, sample_rate=sr)

        self.assertGreater(len(chunks), 5)
        # Verify chunks cover the entire audio length
        total_chunk_samples = sum(len(c["audio"]) for c in chunks)
        self.assertEqual(total_chunk_samples, num_samples)

        # Check timestamp continuity
        for i in range(len(chunks) - 1):
            self.assertAlmostEqual(chunks[i]["end_sec"], chunks[i + 1]["start_sec"], places=2)

    def test_rolling_prompt_context_bounded(self):
        """Verify rolling prompt cache stays within length limit and rejects loops."""
        segments = [
            {"text": "Bugün toplantıda SesMetin-v2 modelini konuştuk."},
            {"text": "Model telefon kayıtlarında yüksek başarı sergiliyor."}
        ]
        context = self.processor.build_rolling_prompt(segments)
        self.assertIsInstance(context, str)
        self.assertLessEqual(len(context), self.processor.max_context_chars)
        self.assertIn("SesMetin-v2", context)

    def test_rolling_prompt_deduplication(self):
        """Verify repetitive segments do not create infinite prompt loops."""
        repeating_segments = [
            {"text": "evet evet evet evet evet evet evet"},
            {"text": "evet evet evet evet evet evet evet"}
        ]
        context = self.processor.build_rolling_prompt(repeating_segments)
        # Should drop or heavily compress repetition loops
        self.assertLess(len(context), 50)


if __name__ == "__main__":
    unittest.main()
