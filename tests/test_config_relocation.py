import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import src
import src.config as config


class TestConfigRelocationAndVersion(unittest.TestCase):
    """Test suite ensuring OS-standard config relocation, legacy migration, version 1.0.7, and minimalist title."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_appdata = os.environ.get("APPDATA")
        self.fake_appdata = Path(self.test_dir) / "AppData" / "Roaming"
        self.fake_appdata.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.orig_appdata is not None:
            os.environ["APPDATA"] = self.orig_appdata
        elif "APPDATA" in os.environ:
            del os.environ["APPDATA"]
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_app_version_is_107(self):
        """Verify APP_VERSION and package version are consistent and at least 1.0.7."""
        from src.updater import SemVer
        self.assertTrue(
            SemVer.parse(config.APP_VERSION) >= SemVer.parse("1.0.7"),
            "config.APP_VERSION must be 1.0.7 or higher"
        )
        self.assertEqual(config.APP_VERSION, src.__version__, "src.__version__ must match config.APP_VERSION")
        self.assertEqual(
            config.DEFAULT_CONFIG["last_seen_version"],
            config.APP_VERSION,
            "DEFAULT_CONFIG last_seen_version must match APP_VERSION",
        )

    def test_config_file_location_is_not_in_base_dir(self):
        """Verify CONFIG_FILE / SETTINGS_FILE is located in OS standard AppData, not BASE_DIR."""
        self.assertNotEqual(
            config.SETTINGS_FILE.parent,
            config.BASE_DIR,
            "Configuration file must not be located in BASE_DIR",
        )
        self.assertIn(
            "SesMetinPro",
            str(config.SETTINGS_FILE),
            "Configuration file path must contain 'SesMetinPro'",
        )
        self.assertEqual(
            config.SETTINGS_FILE.name,
            "config.json",
            "Configuration file name must be config.json",
        )

    def test_save_and_load_settings_does_not_create_settings_json_in_base_dir(self):
        """Verify saving settings never creates settings.json in BASE_DIR."""
        legacy_file = config.BASE_DIR / "settings.json"
        if legacy_file.exists():
            legacy_file.unlink()

        test_settings = config.DEFAULT_CONFIG.copy()
        test_settings["theme"] = "light"
        config.save_settings(test_settings)

        self.assertFalse(
            legacy_file.exists(),
            "BASE_DIR / settings.json must NOT be created when saving settings",
        )
        self.assertTrue(
            config.SETTINGS_FILE.exists(),
            "SETTINGS_FILE must exist in OS config directory",
        )

        loaded = config.load_settings()
        self.assertEqual(loaded.get("theme"), "light")

    def test_legacy_settings_migration_and_removal(self):
        """Verify legacy BASE_DIR / settings.json is migrated and then deleted."""
        legacy_file = config.BASE_DIR / "settings.json"
        try:
            legacy_data = {"theme": "light", "model_size": "medium", "speaker_prefix": "Y"}
            legacy_file.write_text(json.dumps(legacy_data), encoding="utf-8")

            loaded = config.load_settings()
            self.assertEqual(loaded.get("speaker_prefix"), "Y")
            self.assertEqual(loaded.get("model_size"), "medium")
            self.assertFalse(
                legacy_file.exists(),
                "Legacy settings.json in BASE_DIR must be deleted after migration",
            )
        finally:
            if legacy_file.exists():
                legacy_file.unlink()

    def test_title_is_strictly_sesmetin_pro(self):
        """Verify window title and header are strictly minimalist 'SesMetin Pro'."""
        app_file = Path(__file__).resolve().parent.parent / "src" / "ui" / "app.py"
        content = app_file.read_text(encoding="utf-8")

        self.assertIn(
            'page.title = "SesMetin Pro"',
            content,
            "page.title must be strictly 'SesMetin Pro'",
        )
        self.assertNotIn(
            "| Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma İstasyonu",
            content,
            "Header must be minimalist and not include redundant subtitle text",
        )


    def test_spec_does_not_package_settings_json(self):
        """Verify SpeechToText.spec does not attempt to package settings.json."""
        spec_path = Path(__file__).resolve().parent.parent / "SpeechToText.spec"
        self.assertTrue(spec_path.exists(), "SpeechToText.spec must exist")
        content = spec_path.read_text(encoding="utf-8")
        self.assertNotIn(
            "'settings.json'",
            content,
            "SpeechToText.spec must not include settings.json in datas",
        )
        self.assertNotIn(
            '"settings.json"',
            content,
            "SpeechToText.spec must not include settings.json in datas",
        )


if __name__ == "__main__":
    unittest.main()
