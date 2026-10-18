"""Unit tests for UI start transcription action and control integrity."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ui.app import FletSpeechToTextApp
from src.ui.components import SkeletonLoader


class TestUIStartTranscription(unittest.TestCase):
    """Tests ensuring starting transcription handles transcript list and skeleton loading without crashes."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_page = MagicMock()
        self.mock_page.overlay = []
        self.mock_page.services = []
        self.mock_page.run_task = MagicMock(side_effect=lambda fn: fn())

        self.app = FletSpeechToTextApp(self.mock_page)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_transcript_column_alias_exists_and_matches_transcript_list(self):
        """transcript_column must exist on FletSpeechToTextApp and reference transcript_list."""
        self.assertTrue(hasattr(self.app, "transcript_column"))
        self.assertIs(self.app.transcript_column, self.app.transcript_list)

    @patch("threading.Thread")
    def test_02_start_transcription_populates_skeleton_loader_without_attribute_error(self, mock_thread):
        """Clicking start transcription should clear transcript_list and mount SkeletonLoader controls."""
        sample_file = Path(self.temp_dir) / "test.mp3"
        sample_file.write_bytes(b"dummy" * 50)
        self.app.selected_file_path = str(sample_file)

        # Call start_transcription
        self.app.start_transcription()

        # Verify button states
        self.assertTrue(self.app.is_processing)
        self.assertTrue(self.app.btn_start.disabled)
        self.assertFalse(self.app.btn_cancel.disabled)

        # Verify skeleton loader was inserted into transcript_list
        self.assertGreater(len(self.app.transcript_list.controls), 0)
        self.assertIsInstance(self.app.transcript_list.controls[0], SkeletonLoader)

        # Verify worker thread was created
        mock_thread.assert_called_once()

    def test_03_start_transcription_without_media_shows_toast_and_does_not_crash(self):
        """Starting transcription without media source should display toast warning and halt."""
        self.app.selected_file_path = None
        self.app.yt_url_entry.value = ""

        with patch.object(self.app, "_show_toast") as mock_toast:
            self.app.start_transcription()
            mock_toast.assert_called_once()
            self.assertFalse(self.app.is_processing)


if __name__ == "__main__":
    unittest.main()
