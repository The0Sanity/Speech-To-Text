"""Otomatik güncelleme (Auto-Updater) modülü testleri.

Test-First prensibi gereğince bu testler henüz `src/updater.py` yazılmadan önce
beklenen davranışları tanımlar.
"""

import io
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
            self.assertTrue(result is None or not result.is_update_available)

    def test_07_download_file_with_progress(self):
        """Dosya indirme akışı ve ilerleme bildirimi düzgün çalışmalıdır."""
        from src.updater import AutoUpdater
        import io

        updater = AutoUpdater(current_version="1.0.0")
        # Geçerli PE dosya başlığı içeren test verisi
        mock_data = b"MZ" + b"\x00" * 62 + b"PE\x00\x00" + b"\x00" * 2000
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

    def test_11_semver_comprehensive_comparisons(self):
        """SemVer sınıfı tüm sürüm formatlarını (v, beta, build, 4 parçalı) hatasız ayrıştırıp kıyaslamalıdır."""
        from src.updater import SemVer

        # Ayrıştırma
        v1 = SemVer.parse("1.2.3")
        self.assertEqual((v1.major, v1.minor, v1.patch), (1, 2, 3))

        v2 = SemVer.parse("v2.0")
        self.assertEqual((v2.major, v2.minor, v2.patch), (2, 0, 0))

        v3 = SemVer.parse("1.0.0-beta.1")
        self.assertEqual((v3.major, v3.minor, v3.patch), (1, 0, 0))
        self.assertEqual(v3.prerelease, "beta.1")

        # Kıyaslamalar
        self.assertTrue(SemVer.parse("1.0.1") > SemVer.parse("1.0.0"))
        self.assertTrue(SemVer.parse("2.0.0") > SemVer.parse("1.99.99"))
        self.assertTrue(SemVer.parse("1.2.0") > SemVer.parse("1.1.9"))
        self.assertEqual(SemVer.parse("v1.0.0"), SemVer.parse("1.0.0"))
        self.assertFalse(SemVer.parse("1.0.0") > SemVer.parse("1.0.0"))
        # Ön sürüm (prerelease) normal sürümden daha küçük olmalıdır
        self.assertTrue(SemVer.parse("1.0.0-beta") < SemVer.parse("1.0.0"))
        self.assertTrue(SemVer.parse("1.0.0-rc.2") > SemVer.parse("1.0.0-rc.1"))

    def test_12_smart_executable_asset_selection(self):
        """Birden çok varlık (asset) arasından en uygun bağımsız masaüstü .exe seçilmelidir."""
        from src.updater import find_best_executable_asset

        assets_1 = [
            {"name": "checksums.txt", "browser_download_url": "https://example.com/sums", "size": 100},
            {"name": "SpeechToText_Setup.exe", "browser_download_url": "https://example.com/setup.exe", "size": 50000000},
            {"name": "SpeechToText.exe", "browser_download_url": "https://example.com/app.exe", "size": 48000000},
            {"name": "unins000.exe", "browser_download_url": "https://example.com/unins.exe", "size": 1000000},
        ]
        best_1 = find_best_executable_asset(assets_1, app_name="SpeechToText")
        self.assertIsNotNone(best_1)
        self.assertEqual(best_1["name"], "SpeechToText.exe")

        # 64-bit mimari önceliği
        assets_2 = [
            {"name": "SpeechToText_arm64.exe", "browser_download_url": "https://example.com/arm.exe", "size": 40000000},
            {"name": "SpeechToText_x64.exe", "browser_download_url": "https://example.com/x64.exe", "size": 42000000},
        ]
        best_2 = find_best_executable_asset(assets_2, app_name="SpeechToText")
        self.assertIsNotNone(best_2)
        self.assertEqual(best_2["name"], "SpeechToText_x64.exe")

        # Exe varlığı yoksa None
        assets_none = [{"name": "source.zip", "size": 500}]
        self.assertIsNone(find_best_executable_asset(assets_none, app_name="SpeechToText"))

    def test_13_verify_pe_executable_validation(self):
        """İndirilen dosyanın geçerli bir Windows PE çalıştırılabilir (MZ) dosyası olduğu doğrulanmalıdır."""
        from src.updater import verify_pe_executable
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as f_valid:
            # Geçerli PE dosya sihirli baytları: 'MZ'
            f_valid.write(b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100)
            valid_path = Path(f_valid.name)

        with tempfile.NamedTemporaryFile(delete=False) as f_corrupt:
            # Bozuk / HTML hata sayfası
            f_corrupt.write(b"<!DOCTYPE html><html>404 Not Found</html>")
            corrupt_path = Path(f_corrupt.name)

        try:
            self.assertTrue(verify_pe_executable(valid_path))
            self.assertFalse(verify_pe_executable(corrupt_path))
        finally:
            if valid_path.exists():
                valid_path.unlink()
            if corrupt_path.exists():
                corrupt_path.unlink()

    def test_14_verify_checksum_sha256(self):
        """SHA256 sağlama toplamı doğrulaması tam eşleşmede True, hatalıysa False vermelidir."""
        from src.updater import verify_checksum
        import hashlib
        import tempfile

        test_data = b"SpeechToText_Binary_Verification_Test_Bytes_2026"
        expected_hash = hashlib.sha256(test_data).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(test_data)
            p = Path(tf.name)

        try:
            self.assertTrue(verify_checksum(p, expected_hash))
            self.assertFalse(verify_checksum(p, "invalid_hash_00000000000000000000000000000000000000000000000000"))
        finally:
            if p.exists():
                p.unlink()

    def test_15_download_with_cancellation_event(self):
        """İndirme işlemi cancel_event set edildiğinde derhal durmalı ve geçici .part dosyasını silmelidir."""
        from src.updater import AutoUpdater
        import io
        import threading
        import time

        updater = AutoUpdater(current_version="1.0.0")
        cancel_ev = threading.Event()

        class InfiniteStream(io.RawIOBase):
            def readable(self):
                return True

            def read(self, n=-1):
                time.sleep(0.01)
                return b"X" * (n if n > 0 else 1024)

        mock_resp = io.BufferedReader(InfiniteStream())
        mock_resp.headers = {"Content-Length": "10000000"}

        target_path = BASE_DIR / "temp" / "test_cancel.exe"
        part_path = target_path.with_suffix(".part")

        def _cancel_after_delay():
            time.sleep(0.05)
            cancel_ev.set()

        threading.Thread(target=_cancel_after_delay, daemon=True).start()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            success = updater.download_asset(
                "https://example.com/fake.exe",
                target_path,
                cancel_event=cancel_ev,
            )
            self.assertFalse(success)
            self.assertFalse(target_path.exists())
            self.assertFalse(part_path.exists(), "İptal edilen indirmenin .part dosyası silinmelidir!")

    def test_16_github_rate_limit_detection(self):
        """GitHub API HTTP 403 döndüğünde CheckStatus.RATE_LIMITED doğru tespit edilmelidir."""
        from src.updater import AutoUpdater, CheckStatus
        import urllib.error

        updater = AutoUpdater(current_version="1.0.0")

        # 403 Forbidden HTTPError simülasyonu
        mock_fp = io.BytesIO(b'{"message": "API rate limit exceeded"}')
        headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1790000000",
        }
        err = urllib.error.HTTPError(
            url=updater.api_url,
            code=403,
            msg="rate limit exceeded",
            hdrs=headers,
            fp=mock_fp,
        )

        with patch("urllib.request.urlopen", side_effect=err):
            info = updater.check_for_updates()
            self.assertIsNotNone(info)
            self.assertEqual(info.status, CheckStatus.RATE_LIMITED)
            self.assertFalse(info.is_update_available)

    def test_17_windows_self_updater_script_generation(self):
        """Windows yerinde değiştirme betiği (.bat) geri alma (.bak), döngülü bekleme ve çift tırnak koruması içermelidir."""
        from src.updater import WindowsSelfUpdater

        new_exe = Path(r"C:\Users\Test User\AppData\Local\Temp\new_app.exe")
        cur_exe = Path(r"C:\Program Files\SesMetin Pro\SpeechToText.exe")
        pid = 12345

        script = WindowsSelfUpdater.generate_batch_script(
            downloaded_exe=new_exe,
            current_exe=cur_exe,
            pid=pid,
        )

        # Temel koruma kuralları
        self.assertIn(f'TARGET_PID={pid}', script)
        self.assertIn('PID eq %TARGET_PID%', script)
        self.assertIn('set "BACKUP=', script)
        self.assertIn('move /y "%BACKUP%"', script, "Geri alma (rollback) komutu bulunmalıdır!")
        self.assertIn('start ""', script)
        self.assertIn('del /f /q "%~f0"', script)

    def test_18_active_transcription_update_lock(self):
        """Aktif bir transkripsiyon işlemi devam ederken güncelleme başlatılamamalıdır."""
        from src.ui.app import FletSpeechToTextApp
        from src.updater import UpdateInfo, CheckStatus

        mock_page = MagicMock()
        mock_page.overlay = []
        app = FletSpeechToTextApp(mock_page)

        # Aktif işlem simülasyonu
        app.is_transcribing = True

        fake_info = UpdateInfo(
            version="1.5.0",
            tag_name="v1.5.0",
            release_name="v1.5.0",
            release_notes="New release",
            published_at="2026-10-17T00:00:00Z",
            is_update_available=True,
            status=CheckStatus.UPDATE_AVAILABLE,
            has_exe_asset=True,
            download_url="https://example.com/app.exe",
        )

        toasts = []
        app._show_toast = lambda msg, is_error=False: toasts.append((msg, is_error))

        app._show_update_modal(fake_info)

        # Modal açıldığında veya indirme denenirken aktif transkripsiyon uyarısı kontrol edilmelidir
        self.assertTrue(any("devam ederken" in msg for msg, is_err in toasts) or hasattr(app, "_check_can_update"))


if __name__ == "__main__":
    unittest.main()

