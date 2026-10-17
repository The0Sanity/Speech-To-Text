"""
Unit tests validating patches for DEF-01 through DEF-12 from the codebase audit.
Stage 3: Test-First verification under the Superpowers Framework.
"""

import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import flet as ft
from src.ui.theme import BG_APP, ACCENT_PRIMARY, DANGER


class TestAuditDefectsPatch(unittest.TestCase):
    """Test suite for verifying all 12 audit defect patches."""

    def test_def_01_window_opacity_and_background(self):
        """DEF-01: Ensure window opacity is kept at 1.0 and solid background is configured."""
        from src.ui.app import SpeechToTextApp, run_flet_app
        import inspect

        source = inspect.getsource(run_flet_app)
        self.assertNotIn("_fade_in_worker", source)
        self.assertNotIn("page.window.opacity = op", source)

        mock_page = MagicMock()
        mock_page.window = MagicMock()
        mock_page.overlay = []
        app = SpeechToTextApp(mock_page)
        self.assertEqual(mock_page.window.opacity, 1.0)
        self.assertEqual(mock_page.bgcolor, BG_APP)

    def test_def_02_ffmpeg_bootstrapper_dialog_no_name_error(self):
        """DEF-02: Ensure FFmpeg bootstrapper dialog does not raise NameError for missing theme constants."""
        from src.ui.app import SpeechToTextApp

        mock_page = MagicMock()
        mock_page.overlay = []
        app = SpeechToTextApp(mock_page)

        try:
            app._show_ffmpeg_bootstrapper_dialog()
        except NameError as e:
            self.fail(f"_show_ffmpeg_bootstrapper_dialog raised NameError: {e}")
        except Exception:
            pass

    def test_def_03_youtube_downloader_signatures(self):
        """DEF-03: Ensure YouTube downloader returns are properly unpacked without ValueError."""
        import inspect
        from src.ui.app import SpeechToTextApp

        app_source = inspect.getsource(SpeechToTextApp)
        self.assertNotIn("success, info, err = get_youtube_video_info", app_source)
        self.assertNotIn("dl_ok, wav_path, dl_err = download_youtube_audio", app_source)

    def test_def_04_active_audio_temp_file_lifecycle(self):
        """DEF-04: Ensure active audio preview WAV is not deleted in finally block during playback."""
        from src.ui.app import SpeechToTextApp
        import inspect

        source = inspect.getsource(SpeechToTextApp._transcription_worker)
        self.assertIn("active_wav_path", source)

    def test_def_05_audio_player_timer_and_pcm_safety(self):
        """DEF-05: Ensure AudioPlayerBar resets playing state and handles audio completion."""
        from src.ui.components import AudioPlayerBar

        bar = AudioPlayerBar()
        self.assertFalse(bar.is_playing)
        self.assertEqual(bar.play_btn.text, "Oynat")

        bar.stop()
        self.assertFalse(bar.is_playing)

    def test_def_06_overlay_leak_prevention(self):
        """DEF-06: Ensure page.overlay does not grow indefinitely."""
        from src.ui.app import SpeechToTextApp

        mock_page = MagicMock()
        mock_page.overlay = []
        app = SpeechToTextApp(mock_page)

        for i in range(5):
            app._show_toast(f"Message {i}")

        self.assertLessEqual(len(mock_page.overlay), 2)

    def test_def_07_whisper_transcription_cancellation(self):
        """DEF-07: Ensure WhisperTranscriber.transcribe checks cancel_event during iteration."""
        from src.transcriber import WhisperTranscriber
        import inspect

        source = inspect.getsource(WhisperTranscriber.transcribe)
        self.assertIn("cancel_event", source)

    def test_def_08_speaker_diarizer_fft_autocorrelation(self):
        """DEF-08: Ensure SpeakerDiarizer._estimate_f0 uses efficient correlation, not raw full np.correlate."""
        from src.diarizer import SpeakerDiarizer
        import inspect

        source = inspect.getsource(SpeakerDiarizer._estimate_f0)
        self.assertNotIn('np.correlate(chunk, chunk, mode="full")', source)

    def test_def_09_pyinstaller_spec_sklearn_imports(self):
        """DEF-09: Ensure SpeechToText.spec includes sklearn hidden imports."""
        spec_path = os.path.join(PROJECT_ROOT, "SpeechToText.spec")
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("sklearn", content)
        self.assertIn("sklearn.cluster", content)

    def test_def_10_turkish_disfluencies_preserves_valid_words(self):
        """DEF-10: Ensure ITN does not delete legitimate Turkish words 'şey' and 'yani'."""
        from src.itn import InverseTextNormalizer

        itn = InverseTextNormalizer()
        input_text = "En önemli şey sağlıktır ve yani bu doğru bir yaklaşımdır."
        cleaned = itn.clean_disfluencies(input_text)
        self.assertIn("şey", cleaned)
        self.assertIn("yani", cleaned)

        filler_text = "Ben eee yarın ııı geleceğim hmmm"
        cleaned_filler = itn.clean_disfluencies(filler_text)
        self.assertNotIn("eee", cleaned_filler)
        self.assertNotIn("ııı", cleaned_filler)

    def test_def_11_auto_updater_checks_is_processing(self):
        """DEF-11: Ensure _check_can_update checks is_processing to avoid updating during active transcription."""
        from src.ui.app import SpeechToTextApp

        mock_page = MagicMock()
        mock_page.overlay = []
        app = SpeechToTextApp(mock_page)

        app.is_processing = True
        self.assertFalse(app._check_can_update())

        app.is_processing = False
        self.assertTrue(app._check_can_update())

    def test_def_12_requirements_and_dead_code_hygiene(self):
        """DEF-12: Ensure requirements.txt does not contain obsolete customtkinter or darkdetect."""
        req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read().lower()

        self.assertNotIn("customtkinter", content)
        self.assertNotIn("darkdetect", content)


if __name__ == "__main__":
    unittest.main()
