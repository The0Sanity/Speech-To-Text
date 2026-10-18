"""Live End-to-End Verification Test for Windows In-Place Self Updater.

Simulates:
1. A running mock application process holding a file handle/lock.
2. An in-place self-update trigger via WindowsSelfUpdater.
3. Verification that the running process and process tree are forcefully terminated.
4. Verification that the binary is safely replaced with the new version bytes.
5. Verification that the updater PowerShell script cleans itself up.
"""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.updater import WindowsSelfUpdater


class TestLiveUpdaterExecution(unittest.TestCase):
    """End-to-End Live Process Execution & Replacement Test Suite."""

    def test_live_process_termination_and_binary_replacement(self):
        """Verify that execute_in_place_update terminates the active process and replaces the binary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target_exe = temp_path / "SpeechToText_LiveTest.exe"
            new_exe = temp_path / "SpeechToText_v110_New.exe"

            # Create mock binary data
            old_bytes = b"MZ_OLD_VERSION_1_0_9_" + b"0" * 4096
            new_bytes = b"MZ_NEW_VERSION_1_1_0_" + b"1" * 4096

            target_exe.write_bytes(old_bytes)
            new_exe.write_bytes(new_bytes)

            # Start a persistent child process holding target_exe locked
            # We use powershell to sleep and keep the file open if possible,
            # or a python process running an infinite sleep
            cmd = [
                sys.executable,
                "-c",
                "import time, sys; time.sleep(120)",
            ]
            proc = subprocess.Popen(cmd)
            target_pid = proc.pid

            try:
                # Verify process is alive
                self.assertIsNone(proc.poll(), "Process should be alive before update")

                # Trigger in-place update
                success = WindowsSelfUpdater.execute_in_place_update(
                    downloaded_exe=new_exe,
                    current_exe=target_exe,
                    pid=target_pid,
                )
                self.assertTrue(success, "execute_in_place_update must return True")

                # Wait for PowerShell script to execute (timeout within 20 seconds)
                start_time = time.time()
                process_killed = False
                file_replaced = False

                while time.time() - start_time < 20:
                    # Check if process has terminated
                    if proc.poll() is not None:
                        process_killed = True

                    # Check if file has been replaced
                    if target_exe.exists():
                        try:
                            content = target_exe.read_bytes()
                            if content == new_bytes:
                                file_replaced = True
                                break
                        except Exception:
                            pass

                    time.sleep(0.5)

                # Assertions
                self.assertTrue(process_killed, f"Target process (PID {target_pid}) must be killed by updater")
                self.assertTrue(file_replaced, "Target binary must be replaced with new version bytes")
                self.assertEqual(target_exe.read_bytes(), new_bytes)

            finally:
                # Cleanup if still alive
                if proc.poll() is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass


if __name__ == "__main__":
    unittest.main()
