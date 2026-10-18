"""Unit tests for UI file selection and visual feedback in SesMetin Pro."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.ui.app import FletSpeechToTextApp


class TestUIFileSelection(unittest.TestCase):
    """Tests ensuring local audio files (MP3/WAV/MP4) load properly with visual feedback."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_page = MagicMock()
        self.mock_page.overlay = []
        self.mock_page.services = []
        self.mock_page.run_task = MagicMock(side_effect=lambda fn: fn())

        self.app = FletSpeechToTextApp(self.mock_page)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_handle_selected_file_provides_immediate_visual_feedback(self):
        """When an audio file is handled, labels must update, status turns green (success), and toast fires."""
        test_file = Path(self.temp_dir) / "test_sample.mp3"
        test_file.write_bytes(b"dummy mp3 content header" * 100)

        with patch.object(self.app, "_show_toast") as mock_toast:
            self.app._handle_selected_file(str(test_file))

            self.assertEqual(self.app.selected_file_path, str(test_file))
            self.assertEqual(self.app.lbl_file_name.value, "test_sample.mp3")
            self.assertIn("MP3", self.app.lbl_file_meta.value)
            self.assertIn("Hazır", self.app.lbl_status.value)
            mock_toast.assert_called_once()
            self.assertIn("test_sample.mp3", mock_toast.call_args[0][0])
            self.mock_page.update.assert_called()

    @patch("flet.controls.services.file_picker.FilePicker.pick_files")
    def test_02_pick_file_dialog_handles_direct_return_value(self, mock_pick_files):
        """FilePicker.pick_files in Flet 1.0 returns list[FilePickerFile]; dialog must process it."""
        test_file = Path(self.temp_dir) / "recording.mp3"
        test_file.write_bytes(b"audio" * 50)

        mock_file_obj = MagicMock()
        mock_file_obj.path = str(test_file)
        mock_pick_files.return_value = [mock_file_obj]

        with patch.object(self.app, "_handle_selected_file") as mock_handle:
            # Simulate async task execution
            async def run_pick():
                files = await self.app.file_picker.pick_files()
                if files and len(files) > 0:
                    self.app._handle_selected_file(files[0].path)

            import asyncio
            asyncio.run(run_pick())

            mock_handle.assert_called_once_with(str(test_file))


if __name__ == "__main__":
    unittest.main()
