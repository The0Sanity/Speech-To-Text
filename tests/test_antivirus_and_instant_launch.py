import inspect
import sys
import unittest
from pathlib import Path

from src.config import APP_VERSION


class TestAntivirusAndInstantLaunch(unittest.TestCase):
    """Test suite ensuring AV mitigation, UPX elimination, and instant foreground launch."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_version_bump_to_103_or_higher(self):
        """Verify that application version is at least 1.0.3."""
        self.assertTrue(APP_VERSION in ["1.0.3", "1.0.4"], "APP_VERSION must be 1.0.3 or higher")

    def test_version_info_file_exists_and_configured(self):
        """Verify Windows PE version_info.txt exists with proper metadata."""
        version_file = self.root_dir / "version_info.txt"
        self.assertTrue(version_file.exists(), "version_info.txt must exist")
        content = version_file.read_text(encoding="utf-8")
        self.assertTrue(
            "filevers=(1, 0, 3, 0)" in content or "filevers=(1, 0, 4, 0)" in content,
            "version_info.txt must contain valid filevers",
        )
        self.assertIn("CompanyName", content)
        self.assertIn("FileDescription", content)
        self.assertIn("ProductName", content)
        self.assertIn("OriginalFilename", content)

    def test_spec_disables_upx_compression(self):
        """Verify SpeechToText.spec explicitly sets upx=False to prevent AV false positives."""
        spec_path = self.root_dir / "SpeechToText.spec"
        self.assertTrue(spec_path.exists(), "SpeechToText.spec must exist")
        content = spec_path.read_text(encoding="utf-8")
        self.assertIn(
            "upx=False",
            content,
            "SpeechToText.spec must have upx=False to prevent false flags on VirusTotal/Kaspersky",
        )
        self.assertNotIn(
            "upx=True",
            content,
            "SpeechToText.spec must not enable UPX compression",
        )

    def test_spec_links_version_info_resource(self):
        """Verify SpeechToText.spec attaches version_info.txt to the executable."""
        spec_path = self.root_dir / "SpeechToText.spec"
        content = spec_path.read_text(encoding="utf-8")
        self.assertIn(
            "version='version_info.txt'",
            content,
            "SpeechToText.spec must link version='version_info.txt'",
        )

    def test_app_lazy_loads_heavy_ai_modules(self):
        """Verify src/ui/app.py does not import WhisperTranscriber or SpeakerDiarizer at top level."""
        app_file = self.root_dir / "src" / "ui" / "app.py"
        content = app_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        top_lines = lines[:60]
        for line in top_lines:
            self.assertNotIn(
                "from src.transcriber import WhisperTranscriber",
                line,
                "WhisperTranscriber must be lazy-loaded, not imported at top level",
            )
            self.assertNotIn(
                "from src.diarizer import SpeakerDiarizer",
                line,
                "SpeakerDiarizer must be lazy-loaded, not imported at top level",
            )

    def test_app_forces_foreground_focus_on_launch(self):
        """Verify run_flet_app sets window focus and foreground without 0.0 opacity delay."""
        app_file = self.root_dir / "src" / "ui" / "app.py"
        content = app_file.read_text(encoding="utf-8")
        self.assertIn("page.window.focused = True", content)
        self.assertIn("page.window.to_front()", content)
        self.assertNotIn(
            "page.window.opacity = 0.0",
            content,
            "Window must not start with opacity = 0.0 to prevent invisible/background launch",
        )

    def test_components_has_skeleton_loader(self):
        """Verify src/ui/components.py provides SkeletonLoader component."""
        import src.ui.components as comps
        self.assertTrue(
            hasattr(comps, "SkeletonLoader") or hasattr(comps, "SkeletonCard"),
            "src.ui.components must provide a SkeletonLoader or SkeletonCard component",
        )

    def test_ci_workflow_has_code_signing_step(self):
        """Verify .github/workflows/release.yml includes Authenticode code signing."""
        workflow_path = self.root_dir / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text(encoding="utf-8")
        self.assertIn(
            "Set-AuthenticodeSignature",
            content,
            "release.yml must include code signing with Set-AuthenticodeSignature",
        )


if __name__ == "__main__":
    unittest.main()
