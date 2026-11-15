"""The model catalog must only list models that exist and say what they really are.

Measured on 2026-11-15/16: the three SesMetin-v2 model files are byte-identical
to stock Whisper (same SHA-256), the three SesMetin-v1 repositories do not
exist, and the old large-v3-turbo repository id does not exist either.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.catalog import MODEL_CATALOG, get_model_spec, resolve_model_id  # noqa: E402
from src.models.manager import ModelManager  # noqa: E402

LEGACY = {
    "sesmetin-v2-turbo": "large-v3-turbo",
    "sesmetin-v2-small": "small",
    "sesmetin-v2-tiny": "tiny",
    "sesmetin-v1-turbo": "large-v3-turbo",
    "sesmetin-v1-small": "small",
    "sesmetin-v1-tiny": "tiny",
}


class TestCatalog(unittest.TestCase):
    def test_no_relabelled_stock_models(self):
        for model_id, spec in MODEL_CATALOG.items():
            self.assertNotIn("sesmetin", model_id)
            self.assertNotIn("The0Sanity", spec.repo_id)

    def test_repos_are_the_ones_faster_whisper_uses(self):
        from faster_whisper.utils import _MODELS

        for model_id, spec in MODEL_CATALOG.items():
            self.assertEqual(spec.repo_id, _MODELS[model_id], model_id)

    def test_old_settings_still_resolve(self):
        for old, new in LEGACY.items():
            self.assertEqual(resolve_model_id(old), new)
            self.assertEqual(get_model_spec(old).model_id, new)
        self.assertEqual(resolve_model_id("small"), "small")
        self.assertIsNone(get_model_spec("invalid-model-name"))


class TestManager(unittest.TestCase):
    def test_model_downloaded_under_old_name_is_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "models--The0Sanity--sesmetin-v2-small-ct2" / "snapshots" / "abc"
            snapshot.mkdir(parents=True)
            (snapshot / "model.bin").write_bytes(b"weights")
            manager = ModelManager(models_dir=Path(tmp))
            self.assertTrue(manager.is_model_installed("small"))
            self.assertEqual(manager.find_local_model_dir("small"), snapshot)
            self.assertIsNone(manager.find_local_model_dir("tiny"))

    def test_failed_download_is_reported_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(models_dir=Path(tmp))
            with patch("faster_whisper.download_model", side_effect=RuntimeError("404")) as download:
                with self.assertRaises(RuntimeError):
                    manager.download_model("small")
            self.assertEqual(download.call_count, 1)
            self.assertFalse(list(Path(tmp).rglob("sesmetin_v2_config.json")))


if __name__ == "__main__":
    unittest.main()
