"""Unit tests for ModelManager fallback and automated provisioning."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.models.catalog import (
    MODEL_CATALOG,
    ModelCategory,
    ModelSpecification,
    get_model_spec,
)
from src.models.manager import ModelManager


class TestModelManagerProvisioning(unittest.TestCase):
    """Tests for automatic fallback and local provisioning when remote HF repos return 401/404."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelManager(models_dir=Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_catalog_has_fallback_base_spec(self):
        """SesMetin-v2 specifications must define valid base models for fallback."""
        turbo = get_model_spec("sesmetin-v2-turbo")
        self.assertIsNotNone(turbo)
        self.assertTrue(hasattr(turbo, "base_model_id") or hasattr(turbo, "fallback_repo_id"))

    @patch("faster_whisper.download_model")
    def test_02_download_model_automatic_provisioning_on_hf_error(self, mock_fw_download):
        """When downloading proprietary model fails with 401/404, fallback provisions base weights and config."""
        def mock_download_side_effect(repo_or_name, output_dir):
            if "The0Sanity" in repo_or_name:
                # Simulate Hugging Face 401 Client Error
                raise RuntimeError("401 Client Error: Repository Not Found for url")
            # Fallback download succeeds, write mock files
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            (out_p / "model.bin").write_text("mock-binary-weights", encoding="utf-8")
            (out_p / "config.json").write_text("{}", encoding="utf-8")
            (out_p / "vocabulary.json").write_text("{}", encoding="utf-8")
            return str(out_p)

        mock_fw_download.side_effect = mock_download_side_effect

        progress_msgs = []
        def on_progress(val, msg):
            progress_msgs.append((val, msg))

        success = self.manager.download_model("sesmetin-v2-turbo", progress_callback=on_progress)
        self.assertTrue(success)

        # Verify mock_fw_download was called twice: once for proprietary, then for fallback
        self.assertGreaterEqual(mock_fw_download.call_count, 2)

        # Verify model directory has installed files
        model_dir = Path(self.temp_dir) / "sesmetin-v2-turbo"
        self.assertTrue((model_dir / "model.bin").exists())
        self.assertTrue((model_dir / "sesmetin_v2_config.json").exists())
        self.assertTrue(self.manager.is_model_installed("sesmetin-v2-turbo"))

    @patch("faster_whisper.download_model")
    def test_03_download_model_fallback_when_hf_repo_has_no_weights(self, mock_fw_download):
        """When downloading proprietary model downloads only metadata/README without model.bin, fallback triggers."""
        def mock_download_side_effect(repo_or_name, output_dir):
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            if "The0Sanity" in repo_or_name:
                # Simulate remote repo that exists but only contains README/config, no model.bin
                (out_p / "README.md").write_text("metadata only", encoding="utf-8")
                return str(out_p)
            # Fallback download delivers actual binary weights
            (out_p / "model.bin").write_text("mock-binary-weights", encoding="utf-8")
            (out_p / "config.json").write_text("{}", encoding="utf-8")
            return str(out_p)

        mock_fw_download.side_effect = mock_download_side_effect

        success = self.manager.download_model("sesmetin-v2-tiny")
        self.assertTrue(success)

        # Must have fallen back to download base weights
        self.assertGreaterEqual(mock_fw_download.call_count, 2)
        model_dir = Path(self.temp_dir) / "sesmetin-v2-tiny"
        self.assertTrue((model_dir / "model.bin").exists())
        self.assertTrue((model_dir / "sesmetin_v2_config.json").exists())
        self.assertTrue(self.manager.is_model_installed("sesmetin-v2-tiny"))


if __name__ == "__main__":
    unittest.main()

