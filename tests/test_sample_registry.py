"""Unit tests for the non-repeating benchmark SampleRegistry.

Verifies SHA-256 deduplication, training set disjointness, and prevention
of duplicate evaluations in SesMetin Pro benchmarks.
"""

import tempfile
import unittest
from pathlib import Path

from tools.benchmarks.sample_registry import SampleRegistry


class TestSampleRegistry(unittest.TestCase):
    """Test suite for sample deduplication and zero data leakage enforcement."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.registry_file = Path(self.temp_dir) / "test_registry.json"
        self.registry = SampleRegistry(storage_path=self.registry_file)

    def test_add_and_duplicate_detection(self):
        """Verify registry accepts unseen samples and flags duplicates."""
        text = "Bu yepyeni bir test cümlesidir."
        added, reason = self.registry.register_sample(text, split="benchmark")
        self.assertTrue(added)
        self.assertEqual(reason, "registered")

        # Second addition should be rejected as duplicate
        added_dup, reason_dup = self.registry.register_sample(text, split="benchmark")
        self.assertFalse(added_dup)
        self.assertEqual(reason_dup, "duplicate_benchmark")

    def test_normalized_duplicate_detection(self):
        """Verify whitespace and casing differences are normalized for collision detection."""
        text1 = "SesMetin Pro v2 modeli telefon testindedir."
        text2 = "  sesmetin pro v2 modeli telefon testindedir.  "
        self.registry.register_sample(text1, split="benchmark")

        added, reason = self.registry.register_sample(text2, split="benchmark")
        self.assertFalse(added)
        self.assertEqual(reason, "duplicate_benchmark")

    def test_training_corpus_leakage_protection(self):
        """Verify samples present in the training set cannot be re-used in benchmarks."""
        train_sentence = "Toplam maliyet 1500 Türk Lirası olarak belirlendi."
        self.registry.register_sample(train_sentence, split="train")

        added, reason = self.registry.register_sample(train_sentence, split="benchmark")
        self.assertFalse(added)
        self.assertEqual(reason, "leakage_from_training")

    def test_persistence_and_reload(self):
        """Verify registry persists to disk and reloads correctly."""
        self.registry.register_sample("Kalıcı test kaydı bir", split="benchmark")
        self.registry.save()

        new_registry = SampleRegistry(storage_path=self.registry_file)
        self.assertEqual(len(new_registry), 1)
        self.assertTrue(new_registry.is_seen("Kalıcı test kaydı bir"))


if __name__ == "__main__":
    unittest.main()
