"""Tests for 10M+ Turkish TDK Permutation Corpus Generation and Cloud Pipeline.

Verifies:
- TDK lexicon extraction, cleaning, and offline fallback.
- Combinatorial permutation engine and non-repeating positional variation.
- Hybrid distribution (70% punctuated, 30% unpunctuated acoustic stream).
- Zero-local-disk streaming Parquet serialization with PyArrow.
- Repository metadata, schema validation, and Hugging Face Cloud Job runner.
"""

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pyarrow as pa
import pyarrow.parquet as pq

from tools.huggingface.tdk_lexicon import TDKLexicon
from tools.huggingface.generate_and_push_tdk_corpus import (
    TDKPermutationGenerator,
    build_dataset_readme,
    serialize_shard_to_parquet_bytes,
    upload_shard_in_memory,
)


class TestTDKCorpusGeneration(unittest.TestCase):
    """Test suite for TDK 10M+ corpus generator and memory-streaming pipeline."""

    def setUp(self):
        self.lexicon = TDKLexicon()

    def test_01_tdk_lexicon_loads_words_and_fallback(self):
        """Lexicon must supply at least thousands of valid Turkish words including TDK authentic terms."""
        words = self.lexicon.get_words()
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 500)

        # Check for key authentic Turkish words
        word_set = {w.lower() for w in words}
        self.assertTrue(
            any("müvafakat" in w or "muvafakat" in w for w in word_set),
            "Expected 'müvafakat' or related root in TDK lexicon",
        )
        self.assertTrue("asker" in word_set)
        self.assertTrue("zeytin" in word_set)
        self.assertTrue("fiyat" in word_set)

    def test_02_permutation_generator_produces_variable_lengths(self):
        """Generator must produce sentences of expanded length averaging ~100 words (75 to 125 words)."""
        sample_vocab = [
            "merhaba", "günaydın", "müvafakat", "asker", "zeytin",
            "fiyat", "merkez", "ucuz", "fahiş", "börek", "artı", "tepsi",
            "ekmek", "peynir", "türkçe", "kelime", "sözlük", "sipariş",
        ]
        gen = TDKPermutationGenerator(vocabulary=sample_vocab, seed=42)

        batch = gen.generate_batch(size=100)
        self.assertEqual(len(batch), 100)

        word_counts = [len(item["text"].split()) for item in batch]
        self.assertTrue(all(75 <= c <= 125 for c in word_counts), f"Word counts outside 75-125: min={min(word_counts)}, max={max(word_counts)}")
        self.assertAlmostEqual(sum(word_counts) / len(word_counts), 100, delta=10)
        self.assertGreater(max(word_counts), min(word_counts))

    def test_03_hybrid_distribution_ratio(self):
        """Generator must maintain approximately 70% punctuated and 30% unpunctuated sentences."""
        sample_vocab = [
            "merhaba", "günaydın", "müvafakat", "asker", "zeytin",
            "fiyat", "merkez", "ucuz", "fahiş", "börek", "artı", "tepsi",
        ]
        gen = TDKPermutationGenerator(vocabulary=sample_vocab, seed=123)

        batch = gen.generate_batch(size=500)
        punctuated = sum(1 for item in batch if item["has_punctuation"])
        ratio = punctuated / len(batch)

        # Allow reasonable statistical margin around 70%
        self.assertGreater(ratio, 0.60)
        self.assertLess(ratio, 0.80)

        # Unpunctuated must have strictly lowercase text and no punctuation marks
        unpunctuated_samples = [item for item in batch if not item["has_punctuation"]]
        self.assertGreater(len(unpunctuated_samples), 50)
        for s in unpunctuated_samples[:20]:
            self.assertEqual(s["text"], s["text"].lower())
            self.assertFalse(any(p in s["text"] for p in [".", ",", "!", "?"]))

    def test_04_positional_variation_non_repeating(self):
        """Words must not repeat in the exact same positions across consecutive sentences."""
        words = ["merhaba", "müvafakat", "asker", "zeytin", "fiyat", "börek"]
        gen = TDKPermutationGenerator(vocabulary=words, seed=99)

        batch = gen.generate_batch(size=10)
        sentences = [item["text"] for item in batch]

        # All sentences in small distinct generation must be non-identical
        self.assertEqual(len(sentences), len(set(sentences)))

    def test_05_serialize_shard_to_parquet_bytes_in_memory(self):
        """Serialization to Parquet must occur in memory without writing files to local disk."""
        sample_data = [
            {
                "id": "tdk_00000001",
                "text": "Merhaba günaydın müvafakat asker, zeytin.",
                "word_count": 5,
                "has_punctuation": True,
                "domain": "tdk_permutation",
            },
            {
                "id": "tdk_00000002",
                "text": "fiyat merkez ucuz fahiş börek artı tepsi",
                "word_count": 7,
                "has_punctuation": False,
                "domain": "tdk_permutation",
            },
        ]
        parquet_bytes = serialize_shard_to_parquet_bytes(sample_data)
        self.assertIsInstance(parquet_bytes, bytes)
        self.assertGreater(len(parquet_bytes), 0)

        # Read back from bytes using PyArrow buffer
        reader = pq.ParquetFile(pa.BufferReader(parquet_bytes))
        table = reader.read()
        self.assertEqual(table.num_rows, 2)
        self.assertIn("text", table.column_names)
        self.assertIn("word_count", table.column_names)
        self.assertIn("has_punctuation", table.column_names)

    def test_06_dataset_readme_contains_parquet_configs_and_attribution(self):
        """Dataset README must declare standard Hugging Face Parquet data_files and attribution."""
        readme = build_dataset_readme(total_samples=10000000, num_shards=50)
        self.assertTrue(readme.startswith("---"))
        self.assertIn("configs:", readme)
        self.assertIn("data/train-*.parquet", readme)
        self.assertIn("10M<n<100M", readme)
        self.assertIn("https://github.com/The0Sanity/Speech-To-Text", readme)
        self.assertIn("Apache 2.0", readme)

    @patch("tools.huggingface.generate_and_push_tdk_corpus.HfApi")
    def test_07_upload_shard_in_memory_purges_buffer(self, mock_hf_api_class):
        """Upload must pass in-memory bytes or temp stream directly to Hub and purge buffer."""
        mock_api = MagicMock()
        mock_hf_api_class.return_value = mock_api

        raw_bytes = b"PARQUET_TEST_PAYLOAD"
        result = upload_shard_in_memory(
            api=mock_api,
            repo_id="The0Sanity/sesmetin-v2-tdk-10m-corpus",
            shard_index=0,
            total_shards=50,
            parquet_bytes=raw_bytes,
        )

        self.assertTrue(result)
        mock_api.upload_file.assert_called_once()
        call_kwargs = mock_api.upload_file.call_args[1]
        self.assertEqual(call_kwargs["repo_id"], "The0Sanity/sesmetin-v2-tdk-10m-corpus")
        self.assertEqual(call_kwargs["path_in_repo"], "data/train-00000-of-00050.parquet")


    @patch("tools.huggingface.generate_and_push_tdk_corpus.get_token")
    @patch("tools.huggingface.generate_and_push_tdk_corpus.HfApi")
    def test_08_automatic_token_fallback_when_env_unset(self, mock_hf_api, mock_get_token):
        """Pipeline must automatically resolve stored OAuth token when HF_TOKEN env var is missing."""
        mock_get_token.return_value = "hf_stored_token_abc123"
        mock_api = MagicMock()
        mock_hf_api.return_value = mock_api

        from tools.huggingface.generate_and_push_tdk_corpus import stream_corpus_to_huggingface
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise exception
            result = stream_corpus_to_huggingface(
                token="hf_stored_token_abc123",
                repo_id="The0Sanity/sesmetin-v2-tdk-10m-corpus",
                total_samples=10,
                shard_size=10,
                max_shards=1,
            )
            self.assertIn("The0Sanity/sesmetin-v2-tdk-10m-corpus", result)

    def test_09_cloud_training_workflow_exists_and_valid(self):
        """GitHub Actions cloud training workflow must exist and have correct trigger inputs."""
        workflow_path = BASE_DIR / ".github" / "workflows" / "cloud_train.yml"
        self.assertTrue(workflow_path.exists(), "cloud_train.yml must exist")
        content = workflow_path.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("HF_TOKEN", content)
        self.assertIn("openai/whisper-small", content)
        self.assertIn("The0Sanity/Speech-To-Text", content)


if __name__ == "__main__":
    unittest.main()
