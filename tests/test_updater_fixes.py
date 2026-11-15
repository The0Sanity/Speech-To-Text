"""Regression tests for the v1.1.6 auto-updater fixes.

Each test pins one reported failure: the window frozen at 100%, the update
that leaves the old version in place, the checksum that was never checked,
and the release pipeline that published mismatched version numbers.
"""

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.updater import (  # noqa: E402
    AutoUpdater,
    WindowsSelfUpdater,
    is_installed_copy,
    post_update_outcome,
)

ASSETS = [
    {"name": "SpeechToText.exe", "browser_download_url": "https://x/SpeechToText.exe", "size": 10},
    {"name": "SpeechToText-Setup.exe", "browser_download_url": "https://x/SpeechToText-Setup.exe", "size": 20},
]
BODY = "SpeechToText.exe: " + "a" * 64 + "\nSpeechToText-Setup.exe: " + "b" * 64


def _pid_alive(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def _run_ps(script_text: str, folder: Path) -> None:
    script = folder / "u.ps1"
    script.write_text(script_text, encoding="utf-8")
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True,
        timeout=60,
    )


class TestAssetChoice(unittest.TestCase):
    def test_portable_copy_gets_portable_exe(self):
        info = AutoUpdater(current_version="1.1.5").parse_release_payload(
            {"tag_name": "v1.1.6", "assets": ASSETS, "body": BODY}
        )
        self.assertEqual(info.asset_name, "SpeechToText.exe")
        self.assertFalse(info.use_installer)
        self.assertEqual(info.expected_sha256, "a" * 64)

    def test_installed_copy_gets_installer(self):
        updater = AutoUpdater(current_version="1.1.5")
        updater.prefer_installer = True
        info = updater.parse_release_payload({"tag_name": "v1.1.6", "assets": ASSETS, "body": BODY})
        self.assertEqual(info.asset_name, "SpeechToText-Setup.exe")
        self.assertTrue(info.use_installer)
        self.assertEqual(info.expected_sha256, "b" * 64)

    def test_major_bump_always_gets_installer(self):
        info = AutoUpdater(current_version="1.1.6").parse_release_payload(
            {"tag_name": "v2.0.0", "assets": ASSETS, "body": BODY}
        )
        self.assertTrue(info.use_installer)
        self.assertEqual(info.asset_name, "SpeechToText-Setup.exe")

    def test_is_installed_copy_detects_inno_uninstaller(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "SpeechToText.exe"
            exe.write_bytes(b"MZ")
            self.assertFalse(is_installed_copy(exe))
            (Path(tmp) / "unins000.exe").write_bytes(b"MZ")
            self.assertTrue(is_installed_copy(exe))


class TestChecksumIsUsed(unittest.TestCase):
    def test_download_update_passes_release_checksum(self):
        updater = AutoUpdater(current_version="1.1.5")
        info = updater.parse_release_payload({"tag_name": "v1.1.6", "assets": ASSETS, "body": BODY})
        with patch.object(updater, "download_asset", return_value=True) as dl:
            self.assertTrue(updater.download_update(info, Path("x.exe")))
        self.assertEqual(dl.call_args.kwargs["expected_hash"], "a" * 64)


class TestPostUpdateOutcome(unittest.TestCase):
    def test_outcome(self):
        self.assertIsNone(post_update_outcome("1.1.6", None))
        self.assertEqual(post_update_outcome("1.1.6", "1.1.6"), "updated")
        # The swap rolled back: the old version is running again.
        self.assertEqual(post_update_outcome("1.1.5", "1.1.6"), "failed")


class TestScripts(unittest.TestCase):
    def test_swap_script_closes_orphaned_child_windows(self):
        """The app exits with os._exit, which leaves the Flet window process running (frozen at 100%)."""
        # The venv python.exe is a launcher that re-spawns the real interpreter, which would put an
        # extra, already dead process between parent and child. Use the real interpreter directly.
        python = getattr(sys, "_base_executable", sys.executable)
        child_code = "import time; time.sleep(120)"
        parent_code = (
            "import subprocess, sys; "
            f"p = subprocess.Popen([{python!r}, '-c', {child_code!r}]); "
            "print(p.pid, flush=True)"
        )
        parent = subprocess.Popen([python, "-c", parent_code], stdout=subprocess.PIPE, text=True)
        child_pid = int(parent.stdout.readline().strip())
        parent.wait(timeout=10)
        try:
            self.assertTrue(_pid_alive(child_pid))
            with tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                (folder / "Old.exe").write_bytes(b"MZ_OLD")
                (folder / "New.exe").write_bytes(b"MZ_NEW")
                script = WindowsSelfUpdater.generate_powershell_script(
                    folder / "New.exe", folder / "Old.exe", parent.pid, retries=3, log_path=folder / "updater.log"
                )
                _run_ps(script, folder)
                time.sleep(0.5)
                self.assertFalse(_pid_alive(child_pid), "orphaned child window process must be closed")
                self.assertEqual((folder / "Old.exe").read_bytes(), b"MZ_NEW")
                self.assertIn("swap ok", (folder / "updater.log").read_text(encoding="utf-8", errors="replace"))
        finally:
            subprocess.run(["taskkill", "/F", "/PID", str(child_pid)], capture_output=True)

    def test_installer_script_runs_installer_then_relaunches(self):
        script = WindowsSelfUpdater.generate_installer_script(
            Path("C:/t/SpeechToText-Setup.exe"), Path("C:/app/SpeechToText.exe"), 4242, silent=True
        )
        self.assertIn("/VERYSILENT", script)
        self.assertIn("-Wait", script)
        self.assertIn("ParentProcessId", script)

    def test_cross_major_installer_is_interactive(self):
        script = WindowsSelfUpdater.generate_installer_script(
            Path("C:/t/SpeechToText-Setup.exe"), Path("C:/app/SpeechToText.exe"), 4242, silent=False
        )
        self.assertNotIn("/VERYSILENT", script)


class TestReleasePipelineVersions(unittest.TestCase):
    def test_installer_script_has_no_hardcoded_version(self):
        iss = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
        self.assertIn("#ifndef MyAppVersion", iss)
        self.assertIn("#error", iss)

    def test_workflow_has_no_fallback_tag_and_runs_guard(self):
        yml = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertNotIn('"v1.1.1"', yml)
        self.assertIn("check_version_sync.py", yml)
        self.assertIn("/DMyAppVersion=", yml)

    def test_version_guard(self):
        from src.config import APP_VERSION

        guard = [sys.executable, str(ROOT / "scripts" / "check_version_sync.py"), "--tag"]
        self.assertEqual(subprocess.run(guard + [f"v{APP_VERSION}"], capture_output=True).returncode, 0)
        self.assertNotEqual(subprocess.run(guard + ["v9.9.9"], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
