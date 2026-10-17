"""
Unit tests for the enhanced auto-updater mechanism, smooth progress bar,
postponed update persistence on launch, and post-update patch notes modal.
Stage 3: Test-First discipline under Superpowers Framework.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import flet as ft
from src.config import APP_VERSION
from src.updater import CheckStatus, UpdateInfo


class TestEnhancedUpdater(unittest.TestCase):
    """Test suite for enhanced updater and patch notes modal."""

    def setUp(self):
        self.mock_page = MagicMock()
        self.mock_page.overlay = []

    def test_postponed_update_saved_when_later_clicked(self):
        """When user clicks 'Daha Sonra', the update info must be saved as postponed in settings."""
        from src.ui.app import SpeechToTextApp

        with patch("src.ui.app.save_settings") as mock_save:
            app = SpeechToTextApp(self.mock_page)
            test_info = UpdateInfo(
                version="9.9.9",
                tag_name="v9.9.9",
                release_name="v9.9.9 Release",
                release_notes="Super new features",
                published_at="2026-10-20",
                is_update_available=True,
                status=CheckStatus.UPDATE_AVAILABLE,
                download_url="https://example.com/SpeechToText.exe",
                asset_size=50000000,
                has_exe_asset=True,
            )

            # Postpone update
            app._postpone_update(test_info)
            self.assertIn("postponed_update", app.settings)
            self.assertEqual(app.settings["postponed_update"]["version"], "9.9.9")
            mock_save.assert_called()

    def test_postponed_update_prompted_on_launch(self):
        """On startup, if a postponed update is present in settings, it must be prompted to the user."""
        from src.ui.app import SpeechToTextApp

        app = SpeechToTextApp(self.mock_page)
        app.settings["postponed_update"] = {
            "version": "9.9.9",
            "tag_name": "v9.9.9",
            "release_name": "v9.9.9 Release",
            "release_notes": "Postponed update notes",
            "published_at": "2026-10-20",
            "download_url": "https://example.com/SpeechToText.exe",
            "asset_size": 50000000,
            "has_exe_asset": True,
        }

        with patch.object(app, "_show_update_modal") as mock_show_modal:
            prompted = app.check_and_prompt_postponed_update()
            self.assertTrue(prompted)
            mock_show_modal.assert_called_once()
            called_info = mock_show_modal.call_args[0][0]
            self.assertEqual(called_info.version, "9.9.9")

    def test_patch_notes_shown_after_update(self):
        """When app launches after an update, patch notes dialog must be shown and settings updated."""
        from src.ui.app import SpeechToTextApp

        with patch("src.ui.app.save_settings") as mock_save:
            app = SpeechToTextApp(self.mock_page)
            # Simulate older last_seen_version and pending patch notes
            app.settings["last_seen_version"] = "0.9.0"
            app.settings["pending_patch_notes"] = "- Added smooth updater\n- Fixed transparency"

            with patch.object(app, "_show_patch_notes_dialog") as mock_show_notes:
                shown = app.check_and_show_patch_notes()
                self.assertTrue(shown)
                mock_show_notes.assert_called_once()
                self.assertEqual(app.settings["last_seen_version"], app.APP_VERSION)
                self.assertEqual(app.settings["pending_patch_notes"], "")
                mock_save.assert_called()

    def test_smooth_progress_throttling_helper(self):
        """Progress updates must be throttled to prevent Flet WebSocket IPC bridge congestion."""
        from src.ui.app import SpeechToTextApp

        app = SpeechToTextApp(self.mock_page)
        self.assertTrue(hasattr(app, "_create_smooth_progress_handler"))

        updates_received = []

        def mock_ui_updater(progress_val, status_text):
            updates_received.append((progress_val, status_text))

        handler = app._create_smooth_progress_handler(
            total_bytes=1000000,
            ui_updater=mock_ui_updater,
            throttle_interval=0.08,
        )

        # Simulate 100 rapid chunk calls in zero time
        for i in range(1, 101):
            handler(i * 10000, 1000000)

        # Due to throttling, updates_received must be much less than 100 (e.g. initial and final 100%)
        self.assertLess(len(updates_received), 10)
        # But final update must be 1.0 (100%)
        last_update = updates_received[-1]
        self.assertEqual(last_update[0], 1.0)
        self.assertIn("100", last_update[1])


if __name__ == "__main__":
    unittest.main()
