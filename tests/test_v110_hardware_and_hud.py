"""Unit tests for SesMetin Pro v1.1.0 hardware diagnostics, compatibility evaluation, and HUD."""

import unittest
from unittest.mock import MagicMock, patch

from src.hardware import (
    evaluate_model_compatibility,
    resolve_execution_device_and_compute,
)
from src.models.catalog import MODEL_CATALOG, get_model_spec
from src.ui.app import FletSpeechToTextApp


class TestV110HardwareAndHUD(unittest.TestCase):
    """Tests verifying hardware capability detection, model compatibility, and HUD behavior."""

    def test_01_large_v3_exists_in_catalog(self):
        """Official large-v3 model specification must exist in MODEL_CATALOG."""
        self.assertIn("large-v3", MODEL_CATALOG)
        spec = get_model_spec("large-v3")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.model_id, "large-v3")
        self.assertGreaterEqual(spec.ram_req_gb, 5.0)

    def test_02_resolve_execution_device_and_compute_auto(self):
        """Auto mode should resolve to CUDA when available, otherwise CPU INT8."""
        dev, comp = resolve_execution_device_and_compute("auto", cuda_available=True)
        self.assertEqual(dev, "cuda")
        self.assertEqual(comp, "float16")

        dev, comp = resolve_execution_device_and_compute("auto", cuda_available=False)
        self.assertEqual(dev, "cpu")
        self.assertEqual(comp, "int8")

    def test_03_resolve_execution_device_forced_modes(self):
        """Forced CPU and CUDA modes should resolve correctly with fallbacks."""
        dev, comp = resolve_execution_device_and_compute("cpu", cuda_available=True)
        self.assertEqual(dev, "cpu")
        self.assertEqual(comp, "int8")

        # When CUDA is forced but not available, it must gracefully fallback to CPU
        dev, comp = resolve_execution_device_and_compute("cuda", cuda_available=False)
        self.assertEqual(dev, "cpu")
        self.assertEqual(comp, "int8")

    @patch("src.hardware.detect_cuda_capabilities")
    @patch("src.hardware.get_memory_info")
    def test_04_evaluate_model_compatibility_sufficient_memory(self, mock_mem, mock_cuda):
        """Model requiring 2GB RAM on system with 8GB available should be fully compatible."""
        mock_mem.return_value = (16.0, 8.0)
        mock_cuda.return_value = (False, [])

        res = evaluate_model_compatibility("sesmetin-v2-small", mode="auto")
        self.assertEqual(res["status"], "compatible")
        self.assertTrue(res["can_run"])
        self.assertIn("Uyumlu", res["status_label"])

    @patch("src.hardware.detect_cuda_capabilities")
    @patch("src.hardware.get_memory_info")
    def test_05_evaluate_model_compatibility_low_memory(self, mock_mem, mock_cuda):
        """Model requiring 6GB RAM on system with only 1GB available should report warning."""
        mock_mem.return_value = (4.0, 1.0)
        mock_cuda.return_value = (False, [])

        res = evaluate_model_compatibility("large-v3", mode="auto")
        self.assertEqual(res["status"], "tight")
        self.assertIn("Sınır", res["status_label"])

    def test_06_ui_has_hardware_mode_and_hud_controls(self):
        """FletSpeechToTextApp must expose cmb_hardware_mode and hardware_hud_card."""
        mock_page = MagicMock()
        mock_page.overlay = []
        mock_page.services = []
        mock_page.run_task = MagicMock(side_effect=lambda fn: fn())

        app = FletSpeechToTextApp(mock_page)
        self.assertTrue(hasattr(app, "cmb_hardware_mode"))
        self.assertTrue(hasattr(app, "hardware_hud_card"))
        self.assertIsNotNone(app.cmb_hardware_mode.value)

    def test_07_inno_setup_script_exists_and_configured(self):
        """packaging/installer.iss must exist and define proper metadata and output filename."""
        from pathlib import Path
        iss_path = Path("packaging/installer.iss")
        self.assertTrue(iss_path.exists())
        content = iss_path.read_text(encoding="utf-8")
        self.assertIn('#define MyAppVersion "1.1.0"', content)
        self.assertIn("OutputBaseFilename=SpeechToText-Setup", content)
        self.assertIn("ArchitecturesAllowed=x64compatible", content)

    def test_08_release_workflow_contains_dual_packaging(self):
        """.github/workflows/release.yml must produce both portable and setup executables."""
        from pathlib import Path
        wf_path = Path(".github/workflows/release.yml")
        self.assertTrue(wf_path.exists())
        content = wf_path.read_text(encoding="utf-8")
        self.assertIn("iscc.exe", content)
        self.assertIn("dist/SpeechToText.exe", content)
        self.assertIn("dist/SpeechToText-Setup.exe", content)
        self.assertIn("dist/SpeechToText-Setup.exe.sha256", content)

    def test_09_version_synchronization_v110(self):
        """All version references across config, init, and PE info must strictly synchronize to 1.1.0."""
        from pathlib import Path
        import src
        from src.config import APP_VERSION, DEFAULT_CONFIG

        self.assertEqual(APP_VERSION, "1.1.0")
        self.assertEqual(src.__version__, "1.1.0")
        self.assertEqual(DEFAULT_CONFIG.get("last_seen_version"), "1.1.0")
        self.assertEqual(DEFAULT_CONFIG.get("hardware_mode"), "auto")

        ver_info = Path("version_info.txt").read_text(encoding="utf-8")
        self.assertIn("(1, 1, 0, 0)", ver_info)
        self.assertIn("'1.1.0.0'", ver_info)


if __name__ == "__main__":
    unittest.main()
