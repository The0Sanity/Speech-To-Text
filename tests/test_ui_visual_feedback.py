"""Unit tests for UI visual feedback enhancements and Model Hub state corrections."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import flet as ft

from src.models.catalog import MODEL_CATALOG, get_model_spec
from src.models.manager import ModelManager


class TestUIVisualFeedback(unittest.TestCase):
    """Visual feedback and Model Hub state tests."""

    def setUp(self):
        self.mock_model_manager = MagicMock(spec=ModelManager)
        # Simulate tiny is installed, turbo is not installed
        self.mock_model_manager.is_model_installed.side_effect = lambda m: m == "tiny"

    def test_01_model_dropdown_options_have_download_tags(self):
        """Dropdown options must contain [Indirildi] or [Indirilmedi] tags based on installation status."""
        from src.ui.app import build_model_dropdown_options, parse_model_id_from_dropdown_value

        options = build_model_dropdown_options(self.mock_model_manager)
        self.assertGreater(len(options), 5)

        tiny_opt = next((opt for opt in options if parse_model_id_from_dropdown_value(opt.key) == "tiny"), None)
        self.assertIsNotNone(tiny_opt)
        self.assertIn("[İndirildi]", tiny_opt.key)

        turbo_opt = next((opt for opt in options if "large-v3-turbo" in opt.key.lower()), None)
        self.assertIsNotNone(turbo_opt)
        self.assertIn("[İndirilmedi]", turbo_opt.key)

        # Ensure parsing extracts pure model_id
        self.assertEqual(parse_model_id_from_dropdown_value(tiny_opt.key), "tiny")
        self.assertEqual(parse_model_id_from_dropdown_value(turbo_opt.key), "large-v3-turbo")

    def test_02_model_hub_uninstalled_active_model_retains_download_button(self):
        """If an active model is not installed, Model Hub must show 'Indir' button and not claim it is active default."""
        from src.ui.app import resolve_model_card_state

        spec = get_model_spec("sesmetin-v2-turbo")
        self.assertIsNotNone(spec)

        # Case A: Active in dropdown but NOT installed
        state_uninstalled_active = resolve_model_card_state(
            spec=spec,
            current_active_model_id="sesmetin-v2-turbo",
            is_installed=False,
            is_downloading=False,
        )
        self.assertTrue(state_uninstalled_active["show_download_button"])
        self.assertFalse(state_uninstalled_active["is_active_default"])
        self.assertTrue(state_uninstalled_active["is_selected_uninstalled"])

        # Case B: Active in dropdown AND installed
        state_installed_active = resolve_model_card_state(
            spec=spec,
            current_active_model_id="sesmetin-v2-turbo",
            is_installed=True,
            is_downloading=False,
        )
        self.assertFalse(state_installed_active["show_download_button"])
        self.assertTrue(state_installed_active["is_active_default"])
        self.assertTrue(state_installed_active["show_delete_button"])

        # Case C: Installed but not active
        state_installed_inactive = resolve_model_card_state(
            spec=spec,
            current_active_model_id="small",
            is_installed=True,
            is_downloading=False,
        )
        self.assertFalse(state_installed_inactive["show_download_button"])
        self.assertTrue(state_installed_inactive["show_set_default_button"])
        self.assertTrue(state_installed_inactive["show_delete_button"])

        # Case D: Uninstalled and not active
        state_uninstalled_inactive = resolve_model_card_state(
            spec=spec,
            current_active_model_id="small",
            is_installed=False,
            is_downloading=False,
        )
        self.assertTrue(state_uninstalled_inactive["show_download_button"])
        self.assertFalse(state_uninstalled_inactive["show_set_default_button"])

    def test_03_button_visibility_switching(self):
        """Idle state shows Start and hides Cancel. Active state hides Start and shows Cancel."""
        from src.ui.app import determine_transcription_button_visibility

        idle_vis = determine_transcription_button_visibility(is_processing=False)
        self.assertTrue(idle_vis["start_visible"])
        self.assertFalse(idle_vis["cancel_visible"])

        running_vis = determine_transcription_button_visibility(is_processing=True)
        self.assertFalse(running_vis["start_visible"])
        self.assertTrue(running_vis["cancel_visible"])

    def test_04_granular_progress_messages(self):
        """Transcription progress formatter must format stage, percentage, and message without freezing at 1/5."""
        from src.ui.app import format_detailed_progress

        msg1 = format_detailed_progress(step=1, total_steps=5, step_pct=0.45, stage_name="FFmpeg ile ses dönüştürülüyor")
        self.assertIn("[1/5 - %45]", msg1)
        self.assertIn("FFmpeg", msg1)

        msg3 = format_detailed_progress(step=3, total_steps=5, step_pct=None, stage_name="Model RAM/VRAM belleğe yükleniyor")
        self.assertIn("[3/5]", msg3)
        self.assertIn("RAM/VRAM", msg3)


if __name__ == "__main__":
    unittest.main()
