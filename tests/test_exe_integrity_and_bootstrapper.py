"""Executable paketleme butunlugu ve bagimlilik on yukleyici testleri."""

import os
import sys
import tempfile
import unittest
from pathlib import Path


class TestExeIntegrityAndBootstrapper(unittest.TestCase):
    """PyInstaller spec, guvenli stdin ve bagimlilik bootstrapper testleri."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_01_spec_does_not_exclude_unittest(self):
        """SpeechToText.spec icinde unittest asla hariç tutulmamalidir."""
        spec_path = self.root_dir / "SpeechToText.spec"
        self.assertTrue(spec_path.exists(), "SpeechToText.spec dosyasi bulunamadi.")
        spec_content = spec_path.read_text(encoding="utf-8")

        # excludes listesinde unittest olmamali
        self.assertNotIn(
            "'unittest'",
            spec_content.split("excludes=")[1].split("]")[0],
            "unittest modulu excludes listesinden cikarilmalidir.",
        )

        # hiddenimports icinde unittest bulunmali
        self.assertIn(
            "'unittest'",
            spec_content.split("hiddenimports=")[1].split("]")[0],
            "unittest hiddenimports listesine eklenmelidir.",
        )

    def test_02_main_py_guards_stdin_in_windowed_mode(self):
        """main.py windowed (sys.stdin=None) modunda asla RuntimeError: lost sys.stdin firlatmamalidir."""
        main_path = self.root_dir / "main.py"
        self.assertTrue(main_path.exists(), "main.py bulunamadi.")
        main_content = main_path.read_text(encoding="utf-8")

        # Ham input() cagrisi olmamali, stdin kontrolu altinda olmali
        self.assertIn("isatty", main_content, "sys.stdin.isatty kontrolu eklenmelidir.")
        self.assertIn("crash.log", main_content, "Hata aninda crash.log dosyasina yazilmalidir.")

    def test_03_config_frozen_directory_resolution(self):
        """src/config.py PyInstaller dondurulmus modda _MEIPASS yerine kalici dizini kullanmalidir."""
        import src.config as cfg

        self.assertTrue(hasattr(cfg, "get_base_dir"), "config modulunde get_base_dir fonksiyonu bulunmalidir.")
        base_dir = cfg.get_base_dir()
        self.assertIsInstance(base_dir, Path)
        self.assertTrue(base_dir.exists())

    def test_04_bootstrapper_module_and_detection(self):
        """src/bootstrapper.py modulu yuklenebilmeli ve FFmpeg durumunu tespit edebilmelidir."""
        from src.bootstrapper import DependencyBootstrapper

        bootstrapper = DependencyBootstrapper()
        status = bootstrapper.check_ffmpeg_status()
        self.assertIn("installed", status)
        self.assertIn("path", status)
        self.assertIn("version", status)

    def test_05_bootstrapper_appdata_bin_directory(self):
        """Bootstrapper LOCALAPPDATA altindaki ozel bin dizinini tanimalidir."""
        from src.bootstrapper import DependencyBootstrapper

        bootstrapper = DependencyBootstrapper()
        bin_dir = bootstrapper.get_custom_bin_dir()
        self.assertIsInstance(bin_dir, Path)
        self.assertTrue(str(bin_dir).endswith("bin"))

    def test_06_audio_processor_finds_bootstrapper_ffmpeg(self):
        """audio_processor.py bootstrapper tarafindan indirilen ffmpeg.exe dosyasini bulabilmelidir."""
        from src.audio_processor import find_ffmpeg
        from src.bootstrapper import DependencyBootstrapper

        bootstrapper = DependencyBootstrapper()
        custom_bin = bootstrapper.get_custom_bin_dir()
        custom_bin.mkdir(parents=True, exist_ok=True)
        dummy_ffmpeg = custom_bin / "ffmpeg.exe"

        # Gecici sahte dosya olustur ve test et
        try:
            dummy_ffmpeg.touch()
            found = find_ffmpeg()
            self.assertIsNotNone(found, "Bootstrapper ffmpeg dizini tespit edilmeli.")
        finally:
            if dummy_ffmpeg.exists():
                try:
                    dummy_ffmpeg.unlink()
                except OSError:
                    pass

    def test_07_no_emojis_in_spec_and_bootstrapper(self):
        """Yeni veya guncellenen dosyalarda kesinlikle emoji bulunmamalidir."""
        import unicodedata

        files_to_check = [
            self.root_dir / "SpeechToText.spec",
            self.root_dir / "main.py",
            self.root_dir / "src" / "bootstrapper.py",
            self.root_dir / "src" / "config.py",
        ]

        for file_path in files_to_check:
            if not file_path.exists():
                continue
            content = file_path.read_text(encoding="utf-8")
            for char in content:
                category = unicodedata.category(char)
                self.assertFalse(
                    category == "So" or ord(char) > 0x1F000,
                    f"{file_path.name} icinde emoji tespit edildi: {char!r}",
                )


if __name__ == "__main__":
    unittest.main()
