import builtins
import sys
import unittest
from pathlib import Path

import flet
import flet_desktop
import flet_desktop.version

from src.config import APP_VERSION


class TestFletDesktopPackaging(unittest.TestCase):
    """Test suite ensuring standalone executable packaging and Flet desktop dependencies."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_version_bump_to_102(self):
        """Verify that application version is bumped to 1.0.2 for the hotfix."""
        self.assertEqual(APP_VERSION, "1.0.2", "APP_VERSION must be bumped to 1.0.2")

    def test_requirements_includes_flet_desktop(self):
        """Verify requirements.txt explicitly includes flet-desktop."""
        req_path = self.root_dir / "requirements.txt"
        self.assertTrue(req_path.exists(), "requirements.txt must exist")
        content = req_path.read_text(encoding="utf-8")
        self.assertIn(
            "flet-desktop",
            content,
            "requirements.txt must declare flet-desktop dependency",
        )

    def test_flet_desktop_version_matches_flet(self):
        """Verify that flet_desktop version aligns with flet runtime SDK version."""
        self.assertEqual(
            flet_desktop.version.version,
            flet.version.flet_version,
            "flet_desktop version must match flet version to avoid runtime mismatches",
        )

    def test_main_guards_builtins_exit(self):
        """Verify that main.py defines builtins.exit and builtins.quit to prevent NameError."""
        main_path = self.root_dir / "main.py"
        content = main_path.read_text(encoding="utf-8")
        self.assertIn(
            "builtins.exit = sys.exit",
            content,
            "main.py must assign builtins.exit = sys.exit",
        )
        self.assertIn(
            "builtins.quit = sys.exit",
            content,
            "main.py must assign builtins.quit = sys.exit",
        )

    def test_spec_hidden_imports_include_flet_desktop(self):
        """Verify SpeechToText.spec includes flet_desktop submodules in hiddenimports."""
        spec_path = self.root_dir / "SpeechToText.spec"
        self.assertTrue(spec_path.exists(), "SpeechToText.spec must exist")
        content = spec_path.read_text(encoding="utf-8")
        self.assertIn(
            "'flet_desktop'",
            content,
            "SpeechToText.spec must include 'flet_desktop' in hiddenimports",
        )
        self.assertIn(
            "'flet_desktop.version'",
            content,
            "SpeechToText.spec must include 'flet_desktop.version' in hiddenimports",
        )
        self.assertIn(
            "'flet_desktop.win_taskbar'",
            content,
            "SpeechToText.spec must include 'flet_desktop.win_taskbar' in hiddenimports",
        )

    def test_spec_bundles_flet_windows_archive_when_present(self):
        """Verify SpeechToText.spec defines datas mapping for flet-windows.zip."""
        spec_path = self.root_dir / "SpeechToText.spec"
        content = spec_path.read_text(encoding="utf-8")
        self.assertIn(
            "flet_desktop/app",
            content,
            "SpeechToText.spec must map flet-windows.zip to flet_desktop/app",
        )

    def test_ci_workflow_fetches_flet_windows_archive(self):
        """Verify release workflow downloads or caches flet-windows.zip before build."""
        workflow_path = self.root_dir / ".github" / "workflows" / "release.yml"
        self.assertTrue(workflow_path.exists(), "release.yml must exist")
        content = workflow_path.read_text(encoding="utf-8")
        self.assertIn(
            "flet-windows.zip",
            content,
            "release.yml must include step to download flet-windows.zip",
        )


if __name__ == "__main__":
    unittest.main()
