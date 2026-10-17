"""Model kataloğu, SesMetin özel model yapıları ve model yönetici testleri."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.catalog import (
    MODEL_CATALOG,
    ModelCategory,
    ModelSpecification,
    get_model_spec,
    list_available_models,
)
from src.models.manager import ModelManager


class TestModelCatalogAndManager(unittest.TestCase):
    """Model kataloğu ve yerel model yöneticisi işlev testleri."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelManager(models_dir=Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_catalog_has_sesmetin_custom_models(self):
        """Katalogda SesMetin özel modellerinin tanımlı olduğunu doğrula."""
        custom_models = list_available_models(category=ModelCategory.SESMETIN)
        self.assertGreaterEqual(len(custom_models), 3)

        ids = [m.model_id for m in custom_models]
        self.assertIn("sesmetin-v1-turbo", ids)
        self.assertIn("sesmetin-v1-small", ids)
        self.assertIn("sesmetin-v1-tiny", ids)

    def test_02_catalog_has_standard_whisper_models(self):
        """Katalogda standart Faster-Whisper modellerinin yer aldığını doğrula."""
        whisper_models = list_available_models(category=ModelCategory.WHISPER)
        self.assertGreaterEqual(len(whisper_models), 4)

        ids = [m.model_id for m in whisper_models]
        self.assertIn("tiny", ids)
        self.assertIn("base", ids)
        self.assertIn("small", ids)
        self.assertIn("medium", ids)

    def test_03_get_model_spec(self):
        """Model kimliğiyle detaylı özellik sorgulama testi."""
        turbo = get_model_spec("sesmetin-v1-turbo")
        self.assertIsNotNone(turbo)
        self.assertEqual(turbo.category, ModelCategory.SESMETIN)
        self.assertEqual(turbo.version, "1.0.0")
        self.assertTrue(turbo.is_proprietary)

        non_existent = get_model_spec("invalid-model-name")
        self.assertIsNone(non_existent)

    def test_04_model_status_and_installation_check(self):
        """Modelin yerel dizinde olup olmadığının kontrolü."""
        turbo = get_model_spec("sesmetin-v1-turbo")
        self.assertFalse(self.manager.is_model_installed("sesmetin-v1-turbo"))

        # Sahte model dosyası oluştur
        model_dir = Path(self.temp_dir) / "sesmetin-v1-turbo"
        model_dir.mkdir(parents=True)
        (model_dir / "model.bin").write_text("dummy-binary-data", encoding="utf-8")
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / "vocabulary.json").write_text("{}", encoding="utf-8")

        self.assertTrue(self.manager.is_model_installed("sesmetin-v1-turbo"))

    def test_05_disk_usage_calculation(self):
        """Model dizini toplam boyut ve boş disk alanı hesabı testi."""
        # 10 KB sahte dosya yaz
        test_file = Path(self.temp_dir) / "test_model" / "weights.bin"
        test_file.parent.mkdir(parents=True)
        test_file.write_bytes(b"0" * 10240)

        usage = self.manager.get_storage_usage()
        self.assertIn("used_bytes", usage)
        self.assertIn("used_formatted", usage)
        self.assertIn("free_bytes", usage)
        self.assertIn("free_formatted", usage)
        self.assertGreaterEqual(usage["used_bytes"], 10240)

    def test_06_delete_model_safely(self):
        """Model silme işlevi testi."""
        target_dir = Path(self.temp_dir) / "sesmetin-v1-small"
        target_dir.mkdir(parents=True)
        (target_dir / "model.bin").write_text("mock", encoding="utf-8")

        self.assertTrue(target_dir.exists())
        success = self.manager.delete_model("sesmetin-v1-small")
        self.assertTrue(success)
        self.assertFalse(target_dir.exists())


if __name__ == "__main__":
    unittest.main()
