"""Tests for updater PyInstaller environment isolation, file locking, and asset-specific checksum matching.
Stage 3: Test-First discipline under Superpowers Framework.
"""

import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.updater import WindowsSelfUpdater, AutoUpdater, CheckStatus, find_best_executable_asset


class TestUpdaterEnvIsolation(unittest.TestCase):
    """Test suite ensuring complete environment isolation and robust replacement in self-updater."""

    def test_01_execute_in_place_update_scrubs_meipass_and_python_env(self):
        """execute_in_place_update must pass a sanitized env dictionary to subprocess.Popen stripping _MEIPASS2 and Python vars."""
        new_exe = Path(r"C:\fake\new.exe")
        cur_exe = Path(r"C:\fake\cur.exe")
        pid = 12345

        # Simulate running inside PyInstaller one-file bundle with dirty environment
        dirty_env = {
            "PATH": r"C:\Windows\System32",
            "_MEIPASS2": r"C:\Users\test\AppData\Local\Temp\_MEI0000c9942",
            "_MEIPASS": r"C:\Users\test\AppData\Local\Temp\_MEI0000c9942",
            "PYTHONPATH": r"C:\some\path",
            "PYTHONHOME": r"C:\some\home",
            "PYI_PARENT_PID": "9999",
            "PYTHONEXECUTABLE": r"C:\fake\cur.exe",
        }

        with patch.dict(os.environ, dirty_env, clear=True), \
             patch("subprocess.Popen") as mock_popen, \
             patch("builtins.open", unittest.mock.mock_open()):
            success = WindowsSelfUpdater.execute_in_place_update(new_exe, cur_exe, pid)
            self.assertTrue(success)
            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]

            # env must be explicitly passed
            self.assertIn("env", call_kwargs, "execute_in_place_update must explicitly pass sanitized env to subprocess.Popen")
            passed_env = call_kwargs["env"]

            self.assertNotIn("_MEIPASS2", passed_env, "_MEIPASS2 must be purged to prevent child LoadLibrary failure")
            self.assertNotIn("_MEIPASS", passed_env, "_MEIPASS must be purged to prevent child LoadLibrary failure")
            self.assertNotIn("PYTHONPATH", passed_env, "PYTHONPATH must be purged")
            self.assertNotIn("PYTHONHOME", passed_env, "PYTHONHOME must be purged")
            self.assertNotIn("PYI_PARENT_PID", passed_env, "PYI_PARENT_PID must be purged")
            self.assertEqual(passed_env.get("PATH"), r"C:\Windows\System32")

    def test_02_powershell_script_contains_env_var_removal_directives(self):
        """The generated PowerShell script must explicitly clear _MEIPASS2 and _MEIPASS before invoking the new binary."""
        new_exe = Path(r"C:\fake\new.exe")
        cur_exe = Path(r"C:\fake\cur.exe")
        pid = 12345

        script = WindowsSelfUpdater.generate_powershell_script(new_exe, cur_exe, pid)

        # Must explicitly purge _MEIPASS2 and _MEIPASS in PowerShell
        self.assertIn("_MEIPASS2", script, "PowerShell script must explicitly reference and purge _MEIPASS2")
        self.assertIn("_MEIPASS", script, "PowerShell script must explicitly reference and purge _MEIPASS")
        self.assertTrue(
            "Remove-Item" in script and ("_MEIPASS2" in script or "Env:" in script),
            "PowerShell script must remove _MEIPASS2 from environment"
        )

    def test_03_powershell_script_contains_file_lock_wait_and_retry(self):
        """The generated PowerShell script must wait for file lock release and have retry logic on move/backup."""
        new_exe = Path(r"C:\fake\new.exe")
        cur_exe = Path(r"C:\fake\cur.exe")
        pid = 12345

        script = WindowsSelfUpdater.generate_powershell_script(new_exe, cur_exe, pid)

        self.assertIn(".bak", script)
        self.assertIn("Move-Item", script)
        self.assertIn("Start-Sleep", script)
        self.assertIn("Start-Process", script)

    def test_04_release_payload_matches_specific_asset_sha256(self):
        """When release notes contain multiple SHA256 hashes, parse_release_payload must extract the one for SpeechToText.exe."""
        updater = AutoUpdater(current_version="1.1.1")
        payload = {
            "tag_name": "v1.1.2",
            "name": "Speech-To-Text v1.1.2",
            "body": (
                "### Release Notes\n"
                "Updates and features.\n\n"
                "### Checksums (SHA256)\n"
                "- `SpeechToText-Setup.exe`: `1111111111111111111111111111111111111111111111111111111111111111`\n"
                "- `SpeechToText.exe`: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`\n"
            ),
            "assets": [
                {
                    "name": "SpeechToText-Setup.exe",
                    "browser_download_url": "https://example.com/SpeechToText-Setup.exe",
                    "size": 188000000,
                },
                {
                    "name": "SpeechToText.exe",
                    "browser_download_url": "https://example.com/SpeechToText.exe",
                    "size": 187000000,
                },
            ]
        }

        info = updater.parse_release_payload(payload)
        self.assertEqual(info.asset_name, "SpeechToText.exe")
        # Must match the hash for SpeechToText.exe, NOT SpeechToText-Setup.exe
        self.assertEqual(info.expected_sha256, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


if __name__ == "__main__":
    unittest.main()
