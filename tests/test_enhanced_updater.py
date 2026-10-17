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


    def test_update_modal_uses_markdown_and_renders_full_notes(self):
        """Update modal must render full release notes using ft.Markdown instead of truncated ft.Text."""
        from src.ui.app import SpeechToTextApp

        app = SpeechToTextApp(self.mock_page)
        long_notes = "## Header 1\n\n" + "- Feature item\n" * 50
        test_info = UpdateInfo(
            version="1.0.6",
            tag_name="v1.0.6",
            release_name="v1.0.6 Release",
            release_notes=long_notes,
            published_at="2026-10-17",
            is_update_available=True,
            status=CheckStatus.UPDATE_AVAILABLE,
            download_url="https://example.com/SpeechToText.exe",
            asset_size=50000000,
            has_exe_asset=True,
        )

        app._show_update_modal(test_info)

        # Dialog should have been passed to page.open or page.overlay
        opened_dialog = None
        if self.mock_page.open.called:
            opened_dialog = self.mock_page.open.call_args[0][0]
        elif self.mock_page.overlay:
            opened_dialog = self.mock_page.overlay[-1]

        self.assertIsNotNone(opened_dialog)
        # Search for ft.Markdown control inside dialog content
        def find_markdown(control):
            if isinstance(control, ft.Markdown):
                return control
            if hasattr(control, "controls") and control.controls:
                for c in control.controls:
                    found = find_markdown(c)
                    if found:
                        return found
            if hasattr(control, "content") and control.content:
                return find_markdown(control.content)
            return None

        md_control = find_markdown(opened_dialog.content)
        self.assertIsNotNone(md_control, "Modal must use ft.Markdown to render release notes")
        self.assertEqual(md_control.value, long_notes.strip())

    def test_update_modal_button_toggles_during_download(self):
        """When downloading starts, 'Şimdi Güncelle' must be hidden and 'İptal Et' shown."""
        import threading
        from src.ui.app import SpeechToTextApp

        app = SpeechToTextApp(self.mock_page)
        test_info = UpdateInfo(
            version="1.0.6",
            tag_name="v1.0.6",
            release_name="v1.0.6 Release",
            release_notes="Notes",
            published_at="2026-10-17",
            is_update_available=True,
            status=CheckStatus.UPDATE_AVAILABLE,
            download_url="https://example.com/SpeechToText.exe",
            asset_size=50000000,
            has_exe_asset=True,
        )

        app._show_update_modal(test_info)
        opened_dialog = self.mock_page.open.call_args[0][0] if self.mock_page.open.called else self.mock_page.overlay[-1]

        actions = opened_dialog.actions
        # Actions: [btn_github, btn_cancel_download, btn_update, btn_later]
        btn_github = actions[0]
        btn_cancel = actions[1]
        btn_update = actions[2]
        btn_later = actions[3]

        # Initial state before download
        self.assertTrue(btn_update.visible)
        self.assertFalse(btn_cancel.visible)
        self.assertFalse(btn_later.disabled)

        # Trigger download with a blocking event to inspect in-progress state
        download_started = threading.Event()
        continue_download = threading.Event()

        def mock_download(*args, **kwargs):
            download_started.set()
            continue_download.wait(timeout=2)
            return True

        with patch.object(app.updater, "download_asset", side_effect=mock_download):
            btn_update.on_click(None)
            download_started.wait(timeout=2)
            # While downloading: btn_update MUST be hidden, btn_cancel MUST be visible, btn_later disabled
            self.assertFalse(btn_update.visible)
            self.assertTrue(btn_cancel.visible)
            self.assertTrue(btn_later.disabled)

            # Let download complete
            continue_download.set()

    def test_apply_update_calls_os_exit_when_successful(self):
        """apply_update must call os._exit(0) to prevent process hanging or deadlock."""
        from pathlib import Path
        from src.updater import AutoUpdater

        updater = AutoUpdater(current_version="1.0.0")
        with patch("src.updater.WindowsSelfUpdater.execute_in_place_update", return_value=True), \
             patch("sys.frozen", True, create=True), \
             patch("os._exit") as mock_exit, \
             patch.object(Path, "is_file", return_value=True):
            updater.apply_update(Path("dummy.exe"))
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
