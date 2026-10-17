import os
import unittest
from pathlib import Path


class TestFletIconsAndBundling(unittest.TestCase):
    """Test suite ensuring Flet icons and PyInstaller bundle data integrity."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.spec_file = self.root_dir / "SpeechToText.spec"
        self.version_info_file = self.root_dir / "version_info.txt"
        self.config_file = self.root_dir / "src" / "config.py"

    def test_spec_includes_flet_and_dependency_data_files(self):
        """Verify SpeechToText.spec collects flet and runtime data files."""
        self.assertTrue(self.spec_file.exists(), "SpeechToText.spec must exist")
        content = self.spec_file.read_text(encoding="utf-8")

        self.assertIn(
            "collect_data_files",
            content,
            "SpeechToText.spec must import and use collect_data_files",
        )
        self.assertIn(
            "collect_data_files('flet')",
            content,
            "SpeechToText.spec must collect data files for 'flet' to include icons.json",
        )
        self.assertIn(
            "collect_data_files('faster_whisper')",
            content,
            "SpeechToText.spec must collect data files for 'faster_whisper'",
        )

    def test_app_version_bumped_to_104(self):
        """Verify version consistency across configuration and PE metadata."""
        config_content = self.config_file.read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0.4"', config_content, "src/config.py APP_VERSION must be 1.0.4")

        version_info_content = self.version_info_file.read_text(encoding="utf-8")
        self.assertIn("(1, 0, 4, 0)", version_info_content, "version_info.txt must be 1.0.4.0")
        self.assertIn("'1.0.4.0'", version_info_content, "version_info.txt StringFileInfo must be 1.0.4.0")

    def test_runtime_icons_self_healing_resilience(self):
        """Verify that Flet icons remain functional and do not raise FileNotFoundError."""
        import flet as ft
        import flet.controls.material.icons as mat_icons

        # Call our self-healing patch helper
        import main
        self.assertTrue(hasattr(main, "ensure_flet_icons_available"), "main.py must expose ensure_flet_icons_available")
        main.ensure_flet_icons_available()

        # Access icons used in UI
        code_icon = ft.Icons.CODE
        copy_icon = ft.Icons.COPY
        self.assertIsNotNone(code_icon, "ft.Icons.CODE must resolve properly")
        self.assertIsNotNone(copy_icon, "ft.Icons.COPY must resolve properly")


if __name__ == "__main__":
    unittest.main()
