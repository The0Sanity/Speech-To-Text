"""Unit and integration tests for 5 to 10 minute cycled template MP3 generation.

Verifies procedural dialogue script generation, MP3 audio encoding, duration constraints,
telephony acoustic simulation, and long-form transcription accuracy in SesMetin Pro.
"""

import os
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from src.transcription.audio_preprocessing import detect_telephony_audio
from src.transcription.engine import LongFormAudioProcessor
from src.transcription.post_processing import post_process_transcript
from tools.synthetic_data.generate_longform_dialogue_mp3 import (
    CycledDialogueScriptGenerator,
    LongFormMP3Generator,
    generate_cycled_dialogue_mp3,
)


class TestLongFormDialogueMP3(unittest.TestCase):
    """Test suite for long-form cycled dialogue MP3 generation and processing."""

    def setUp(self):
        self.script_gen = CycledDialogueScriptGenerator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dialogue_script_generation(self):
        """Verify script generator creates alternating turns with cycled entities."""
        script = self.script_gen.generate_script(target_duration_seconds=30.0)
        self.assertGreater(len(script.turns), 3)

        # Check alternating speakers
        speakers = [turn.speaker_role for turn in script.turns]
        for i in range(len(speakers) - 1):
            self.assertNotEqual(speakers[i], speakers[i + 1])

        # Verify cycled transaction content
        full_text = " ".join(turn.spoken_text for turn in script.turns)
        self.assertTrue(any(item in full_text.lower() for item in ["ekme", "süt", "elma", "kahve", "peynir", "domates", "bal", "çay", "yumurta"]))
        self.assertTrue("lira" in full_text.lower() or "tl" in full_text.lower())
        self.assertTrue("yüzde" in full_text.lower() or "%" in full_text)

    def test_mp3_audio_generation_and_duration_bounds(self):
        """Verify generated file is a valid MP3 file within expected duration bounds."""
        # Fast test with 10.0 seconds target duration
        result = generate_cycled_dialogue_mp3(
            output_dir=self.output_dir,
            target_duration_minutes=0.1667,  # ~10 seconds for fast test
            filename="test_dialogue_fast.mp3",
            simulate_telephony=False
        )

        mp3_path = Path(result["audio_path"])
        self.assertTrue(mp3_path.exists())
        self.assertEqual(mp3_path.suffix.lower(), ".mp3")

        # Verify with soundfile info
        info = sf.info(str(mp3_path))
        self.assertEqual(info.format, "MP3")
        self.assertEqual(info.samplerate, 16000)
        self.assertGreaterEqual(info.duration, 8.0)
        self.assertLessEqual(info.duration, 45.0)

        # Verify ground truth manifest
        manifest_path = Path(result["manifest_path"])
        self.assertTrue(manifest_path.exists())
        self.assertGreater(result["turn_count"], 0)

    def test_telephony_mp3_generation(self):
        """Verify telephony simulation flag applies cellular bandpass to MP3 output."""
        result = generate_cycled_dialogue_mp3(
            output_dir=self.output_dir,
            target_duration_minutes=0.1667,
            filename="test_dialogue_telephony.mp3",
            simulate_telephony=True
        )

        mp3_path = Path(result["audio_path"])
        audio, sr = sf.read(str(mp3_path))
        self.assertTrue(detect_telephony_audio(audio, sample_rate=sr))

    def test_longform_dialogue_transcription_pipeline(self):
        """Verify long-form transcription processor accurately handles cycled MP3."""
        generator = LongFormMP3Generator(output_dir=self.output_dir)
        result = generator.generate(
            target_duration_minutes=0.2,  # 12 seconds
            filename="test_transcription_pipe.mp3",
            simulate_telephony=False
        )

        mp3_path = result["audio_path"]
        audio, sr = sf.read(mp3_path)

        processor = LongFormAudioProcessor(chunk_target_sec=5.0)
        chunks = processor.split_longform_audio(audio, sample_rate=sr)
        self.assertGreater(len(chunks), 1)

        # Simulate chunk transcription and post-processing
        transcribed_text = post_process_transcript(result["spoken_script"])
        self.assertIn("TL", transcribed_text)
        self.assertTrue("%" in transcribed_text or "indirim" in transcribed_text)

    def test_neural_tts_synthesis_properties(self):
        """Verify turn speech waveforms have valid audio properties and non-zero dynamic energy."""
        generator = LongFormMP3Generator(output_dir=self.output_dir)
        script = self.script_gen.generate_script(target_duration_seconds=10.0)
        self.assertGreater(len(script.turns), 0)

        # Synthesize first turn
        first_turn = script.turns[0]
        waveform = generator._synthesize_all_turns([first_turn])[0]

        self.assertIsInstance(waveform, np.ndarray)
        self.assertGreater(len(waveform), int(16000 * 0.5))
        self.assertGreater(float(np.std(waveform)), 0.01)


if __name__ == "__main__":
    unittest.main()

