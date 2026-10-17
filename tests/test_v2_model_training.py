"""SesMetin-v2 model eğitimi, sentetik veri yükleyici ve değerlendirme testleri."""

import json
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
    get_model_spec,
    list_available_models,
)
from tools.model_training.train_v2_model import (
    SesMetinV2Trainer,
    SyntheticDatasetLoader,
    TrainingConfigV2,
)
from tools.model_training.evaluate_wer import calculate_wer


class TestSesMetinV2ModelTraining(unittest.TestCase):
    """SesMetin-v2 model eğitim hattı ve katalog entegrasyonu testleri."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_v2_models_registered_in_catalog(self):
        """SesMetin-v2 modellerinin katalogda v2 sürümüyle yer aldığını doğrula."""
        v2_turbo = get_model_spec("sesmetin-v2-turbo")
        self.assertIsNotNone(v2_turbo)
        self.assertTrue(v2_turbo.version.startswith("2."))
        self.assertTrue(v2_turbo.is_proprietary)
        self.assertIn("v2", v2_turbo.name.lower())

        v2_small = get_model_spec("sesmetin-v2-small")
        self.assertIsNotNone(v2_small)
        self.assertTrue(v2_small.version.startswith("2."))

        v2_tiny = get_model_spec("sesmetin-v2-tiny")
        self.assertIsNotNone(v2_tiny)
        self.assertTrue(v2_tiny.version.startswith("2."))

    def test_02_synthetic_dataset_loader(self):
        """Sentetik ses veri setinin JSONL manifest dosyasından doğru yüklendiğini doğrula."""
        manifest_file = Path(self.temp_dir) / "synthetic_dataset.jsonl"
        items = [
            {"audio_path": "sample1.wav", "text": "Yapay zeka ses tanıma testi.", "duration": 2.4},
            {"audio_path": "sample2.wav", "text": "SesMetin v2 modeli ile yüksek doğruluk.", "duration": 3.1},
        ]
        with open(manifest_file, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        loader = SyntheticDatasetLoader(manifest_path=manifest_file)
        samples = loader.load_all()
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["text"], "Yapay zeka ses tanıma testi.")
        self.assertEqual(samples[1]["duration"], 3.1)

    def test_03_trainer_config_and_pipeline(self):
        """Eğitim yapılandırması ve hazırlık adımlarının doğruluğu testi."""
        cfg = TrainingConfigV2(
            model_id="sesmetin-v2-small",
            base_model="openai/whisper-small",
            output_dir=os.path.join(self.temp_dir, "v2_output"),
            epochs=3,
            learning_rate=5e-4,
        )
        trainer = SesMetinV2Trainer(config=cfg)
        self.assertIsNotNone(trainer)
        self.assertEqual(trainer.config.model_id, "sesmetin-v2-small")

    def test_04_ground_truth_wer_evaluation(self):
        """Ground-truth metin ile hipotez arasındaki WER değerlendirme testi."""
        ground_truth = "sesmetin v2 modeli sentetik sesle eğitildi"
        perfect_hypothesis = "sesmetin v2 modeli sentetik sesle eğitildi"
        imperfect_hypothesis = "sesmetin v2 modeli sentetik sesle egitildi"

        wer_zero = calculate_wer(ground_truth, perfect_hypothesis)
        self.assertEqual(wer_zero, 0.0)

        wer_imperfect = calculate_wer(ground_truth, imperfect_hypothesis)
        self.assertGreater(wer_imperfect, 0.0)


if __name__ == "__main__":
    unittest.main()
