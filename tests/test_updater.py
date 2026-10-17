"""Otomatik güncelleme (Auto-Updater) modülü testleri.

Test-First prensibi gereğince bu testler henüz `src/updater.py` yazılmadan önce
beklenen davranışları tanımlar.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestAutoUpdater(unittest.TestCase):
    """GitHub Releases üzerinden .exe otomatik güncelleme motoru testleri."""

    def test_01_import_updater_module(self):
        """src.updater modülü başarıyla içe aktarılabilmelidir."""
        import src.updater as updater
        self.assertTrue(hasattr(updater, "AutoUpdater"))
        self.assertTrue(hasattr(updater, "UpdateInfo"))

    def test_02_parse_version_and_compare(self):
        """Sürüm numaralarını (SemVer / vX.Y.Z) doğru ayrıştırmalı ve kıyaslamalıdır."""
        from src.updater import parse_version, is_newer_version

        # Temel sürüm ayrıştırma
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("2.1.0-beta"), (2, 1, 0))

        # Sürüm kıyaslama
        self.assertTrue(is_newer_version("1.0.0", "1.0.1"))
        self.assertTrue(is_newer_version("v1.0.0", "v1.1.0"))
        self.assertTrue(is_newer_version("1.0.0", "2.0.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("v2.0.0", "v1.9.9"))

    def test_03_find_exe_asset_in_release_data(self):
        """GitHub Release JSON verisinden .exe uzantılı dosyayı ve indirme bağlantısını bulmalıdır."""
        from src.updater import AutoUpdater

        mock_release = {
            "tag_name": "v1.1.0",
            "name": "SesMetin Pro v1.1.0",
            "body": "Yeni Flet arayuzu ve gelistirmeler.",
            "published_at": "2026-10-17T12:00:00Z",
            "assets": [
                {
                    "name": "checksums.txt",
                    "browser_download_url": "https://github.com/The0Sanity/Speech-To-Text/releases/download/v1.1.0/checksums.txt",
                    "size": 128,
                },
                {
                    "name": "SpeechToText.exe",
                    "browser_download_url": "https://github.com/The0Sanity/Speech-To-Text/releases/download/v1.1.0/SpeechToText.exe",
                    "size": 45000000,
                },
            ],
        }

        updater = AutoUpdater(current_version="1.0.0")
        update_info = updater.parse_release_payload(mock_release)

        self.assertIsNotNone(update_info)
        self.assertEqual(update_info.version, "1.1.0")
        self.assertEqual(update_info.asset_name, "SpeechToText.exe")
        self.assertEqual(
            update_info.download_url,
            "https://github.com/The0Sanity/Speech-To-Text/releases/download/v1.1.0/SpeechToText.exe",
        )
        self.assertEqual(update_info.asset_size, 45000000)
        self.assertTrue(update_info.is_update_available)

    def test_04_handle_no_exe_asset(self):
        """Release içinde .exe asset yoksa güvenli şekilde ele alınmalıdır."""
        from src.updater import AutoUpdater

        mock_release = {
            "tag_name": "v1.1.0",
            "name": "SesMetin Pro v1.1.0",
            "body": "Sadece kaynak kod yayinlandi.",
            "published_at": "2026-10-17T12:00:00Z",
            "assets": [
                {
                    "name": "source.zip",
                    "browser_download_url": "https://example.com/source.zip",
                    "size": 1000,
                }
            ],
        }

        updater = AutoUpdater(current_version="1.0.0")
        update_info = updater.parse_release_payload(mock_release)

        self.assertIsNotNone(update_info)
        self.assertTrue(update_info.is_update_available)
        self.assertIsNone(update_info.download_url)
        self.assertFalse(update_info.has_exe_asset)

    def test_05_handle_already_up_to_date(self):
        """Mevcut sürüm güncel veya daha yeniyse güncelleme sunulmamalıdır."""
        from src.updater import AutoUpdater

        mock_release = {
            "tag_name": "v1.0.0",
            "name": "SesMetin Pro v1.0.0",
            "body": "Ilk surum.",
            "published_at": "2026-10-17T10:00:00Z",
            "assets": [
                {
                    "name": "SpeechToText.exe",
                    "browser_download_url": "https://example.com/SpeechToText.exe",
                    "size": 45000000,
                }
            ],
        }

        updater = AutoUpdater(current_version="1.0.0")
        update_info = updater.parse_release_payload(mock_release)

        self.assertIsNotNone(update_info)
        self.assertFalse(update_info.is_update_available)

    def test_06_check_updates_network_error(self):
        """Ağ hatasında veya internet kesintisinde uygulama çökmemeli, None veya hata bilgisi dönmelidir."""
        from src.updater import AutoUpdater

        updater = AutoUpdater(current_version="1.0.0")

        with patch("urllib.request.urlopen", side_effect=Exception("Baglanti hatasi")):
            result = updater.check_for_updates()
            self.assertIsNone(result)

    def test_07_download_file_with_progress(self):
        """Dosya indirme akışı ve ilerleme bildirimi düzgün çalışmalıdır."""
        from src.updater import AutoUpdater
        import io

        updater = AutoUpdater(current_version="1.0.0")
        mock_data = b"MOCK_EXE_BINARY_DATA_FOR_TESTING" * 100
        progress_events = []

        def on_progress(downloaded, total):
            progress_events.append((downloaded, total))

        mock_response = io.BytesIO(mock_data)
        mock_response.headers = {"Content-Length": str(len(mock_data))}

        with patch("urllib.request.urlopen", return_value=mock_response):
            target_path = BASE_DIR / "temp" / "test_download.exe"
            try:
                success = updater.download_asset("https://example.com/fake.exe", target_path, on_progress)
                self.assertTrue(success)
                self.assertTrue(target_path.is_file())
                self.assertEqual(target_path.stat().st_size, len(mock_data))
                self.assertGreater(len(progress_events), 0)
            finally:
                if target_path.exists():
                    target_path.unlink()

    def test_08_no_emojis_in_updater_module(self):
        """src/updater.py modülünde kesinlikle hiçbir emoji bulunmamalıdır."""
        updater_file = BASE_DIR / "src" / "updater.py"
        if not updater_file.exists():
            self.fail("src/updater.py henuz olusturulmadi.")

        import re
        content = updater_file.read_text(encoding="utf-8")
        emoji_pattern = re.compile(
            r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
        )
        self.assertFalse(bool(emoji_pattern.search(content)), "src/updater.py icinde emoji bulunmamalidir!")

    def test_09_ui_updater_thread_safe_without_run_task_coroutine_error(self):
        """Flet sayfasında run_task coroutine zorunluluğunda TypeError vermemelidir."""
        from src.ui.app import FletSpeechToTextApp
        from src.updater import UpdateInfo
        import threading
        import time

        mock_page = MagicMock()
        def mock_run_task(handler, *args, **kwargs):
            import inspect
            if not inspect.iscoroutinefunction(handler):
                raise TypeError("handler must be a coroutine function")

        mock_page.run_task = mock_run_task
        mock_page.overlay = []

        app = FletSpeechToTextApp(mock_page)

        fake_info = UpdateInfo(
            version="1.2.0",
            tag_name="v1.2.0",
            release_name="v1.2.0",
            release_notes="Notes",
            published_at="2026-10-17T00:00:00Z",
            is_update_available=True,
            download_url="https://example.com/app.exe",
            asset_name="SpeechToText.exe",
            asset_size=1000,
            has_exe_asset=True,
        )

        with patch.object(app.updater, "check_for_updates", return_value=fake_info):
            # check_updates_dialog çağrıldığında TypeError fırlatılmamalıdır
            try:
                app.check_updates_dialog(manual=True)
                time.sleep(0.3)
            except TypeError as te:
                self.fail(f"check_updates_dialog TypeError firlatti: {te}")

    def test_10_ui_startup_check_shows_modal_when_update_available(self):
        """Uygulama açılışında yeni sürüm varsa doğrudan güncelleme kutusunu açmalıdır."""
        from src.ui.app import FletSpeechToTextApp
        from src.updater import UpdateInfo
        import time

        mock_page = MagicMock()
        mock_page.overlay = []

        app = FletSpeechToTextApp(mock_page)

        fake_info = UpdateInfo(
            version="2.0.0",
            tag_name="v2.0.0",
            release_name="v2.0.0",
            release_notes="Major update",
            published_at="2026-10-17T00:00:00Z",
            is_update_available=True,
            download_url="https://example.com/app.exe",
            asset_name="SpeechToText.exe",
            asset_size=2000,
            has_exe_asset=True,
        )

        modal_shown = []
        app._show_update_modal = lambda info: modal_shown.append(info)

        with patch.object(app.updater, "check_for_updates", return_value=fake_info):
            app.start_background_update_check()
            time.sleep(0.3)

        self.assertEqual(len(modal_shown), 1)
        self.assertEqual(modal_shown[0].version, "2.0.0")


if __name__ == "__main__":
    unittest.main()
