"""Sistem donanım tanı ve CUDA yetenekleri testleri."""

import unittest
from unittest.mock import patch
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.hardware import (
    get_system_hardware_info,
    format_memory_size,
    has_avx2_support,
    get_recommended_device_and_compute,
)


class TestHardwareDiagnostics(unittest.TestCase):
    """Donanım tespit fonksiyonlarının güvenilirlik ve doğruluk testleri."""

    def test_01_get_system_hardware_info_structure(self):
        """Donanım bilgi sözlüğünün gerekli alanları eksiksiz içerdiğini doğrula."""
        info = get_system_hardware_info()
        self.assertIsInstance(info, dict)
        self.assertIn("cpu_name", info)
        self.assertIn("cpu_count", info)
        self.assertIn("avx2_support", info)
        self.assertIn("ram_total_gb", info)
        self.assertIn("ram_available_gb", info)
        self.assertIn("cuda_available", info)
        self.assertIn("cuda_devices", info)
        self.assertIn("recommended_device", info)
        self.assertIn("recommended_compute_type", info)

    def test_02_format_memory_size(self):
        """Bellek boyutu biçimlendirme testi."""
        self.assertEqual(format_memory_size(500), "500.0 B")
        self.assertEqual(format_memory_size(1024), "1.0 KB")
        self.assertEqual(format_memory_size(1024 * 1024 * 150), "150.0 MB")
        self.assertEqual(format_memory_size(1024 * 1024 * 1024 * 2), "2.0 GB")

    def test_03_has_avx2_support_boolean(self):
        """AVX2 tespitinin mantıksal değer döndürdüğünü doğrula."""
        support = has_avx2_support()
        self.assertIsInstance(support, bool)

    def test_04_device_recommendation_logic(self):
        """CUDA var veya yok durumlarına göre doğru cihaz tavsiyesi testi."""
        # CUDA yokken CPU ve INT8 tavsiye edilmeli
        dev_cpu, compute_cpu = get_recommended_device_and_compute(cuda_available=False)
        self.assertEqual(dev_cpu, "cpu")
        self.assertEqual(compute_cpu, "int8")

        # CUDA varken cuda ve float16 tavsiye edilmeli
        dev_cuda, compute_cuda = get_recommended_device_and_compute(cuda_available=True)
        self.assertEqual(dev_cuda, "cuda")
        self.assertEqual(compute_cuda, "float16")


if __name__ == "__main__":
    unittest.main()
