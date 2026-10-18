"""Unit tests for robust multi-tier clipboard copying in SesMetin Pro."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ui.app import copy_to_system_clipboard, FletSpeechToTextApp


class TestClipboard(unittest.TestCase):
    """Test suite for clipboard copying functionality."""

    def test_copy_to_system_clipboard_plain_text(self):
        """Test copying simple non-empty text to system clipboard."""
        sample_text = "SesMetin Pro Turkce Transkripsiyon Pano Testi"
        result = copy_to_system_clipboard(sample_text)
        self.assertTrue(result, "copy_to_system_clipboard should return True for valid text")

    def test_copy_to_system_clipboard_empty_text(self):
        """Test handling of empty string input."""
        self.assertFalse(copy_to_system_clipboard(""), "Empty string should return False")
        self.assertFalse(copy_to_system_clipboard("   \n\t  "), "Whitespace-only string should return False")

    def test_app_copy_to_clipboard_no_set_clipboard_attribute(self):
        """Test that copy_to_clipboard does NOT raise AttributeError when Page lacks set_clipboard."""
        mock_page = MagicMock()
        # Explicitly delete set_clipboard to simulate Flet 1.0.4 Page object
        if hasattr(mock_page, "set_clipboard"):
            delattr(mock_page, "set_clipboard")

        mock_page.services = []
        mock_page.run_task = MagicMock()

        app = FletSpeechToTextApp(page=mock_page)
        app._show_toast = MagicMock()

        # Should not raise AttributeError: 'Page' object has no attribute 'set_clipboard'
        try:
            app.copy_to_clipboard(custom_text="Test Transkript Metni")
        except AttributeError as e:
            self.fail(f"copy_to_clipboard raised AttributeError: {e}")

        # Toast notification should be shown
        app._show_toast.assert_called_with("Panoya kopyalandı!", is_error=False)

    def test_app_copy_to_clipboard_from_transcribed_data(self):
        """Test formatting transcribed segments into speaker-formatted text and copying."""
        mock_page = MagicMock()
        mock_page.services = []
        mock_page.run_task = MagicMock()

        app = FletSpeechToTextApp(page=mock_page)
        app._show_toast = MagicMock()
        app.transcribed_data = [
            {"speaker": "Konusmaci 1", "start": 0.0, "end": 2.5, "text": "Merhaba dunya"},
            {"speaker": "Konusmaci 2", "start": 3.0, "end": 5.0, "text": "SesMetin Pro devrede"},
        ]

        app.copy_to_clipboard()
        app._show_toast.assert_called_with("Panoya kopyalandı!", is_error=False)


if __name__ == "__main__":
    unittest.main()
