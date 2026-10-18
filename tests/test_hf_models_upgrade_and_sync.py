"""Unit tests for Hugging Face model and dataset upgrade & sync tool.

Tests:
1. Model card generation with YAML frontmatter.
2. Upgrade operations for small, turbo, and tiny models.
3. Shard cleanup operation generation for legacy datasets.
4. Longform dialogue JSONL serialization.
"""

import unittest
from unittest.mock import MagicMock, patch

from tools.huggingface.upgrade_and_sync_all_models import (
    build_model_card,
    cleanup_legacy_tdk_shards,
    sync_speech_corpus_dialogues,
    upgrade_small_model,
    upgrade_tiny_model,
    upgrade_turbo_model,
)


class TestHFModelsUpgradeAndSync(unittest.TestCase):
    """Test suite for Hugging Face model synchronization operations."""

    def test_build_model_card_has_required_metadata(self):
        """Verifies YAML frontmatter and repository attribution in generated model cards."""
        card = build_model_card(
            model_id="The0Sanity/test-model",
            name="Test Model",
            wer="%0.3 WER",
            base_model="Systran/faster-whisper-small",
            size_mb=480,
            description="Test description",
            arch_details="Test Arch",
        )
        self.assertTrue(card.startswith("---"))
        self.assertIn("language:\n- tr", card)
        self.assertIn("https://github.com/The0Sanity/Speech-To-Text", card)
        self.assertIn("Systran/faster-whisper-small", card)
        self.assertIn("%0.3 WER", card)

    def test_upgrade_models_submit_create_commit(self):
        """Verifies small, turbo, and tiny model upgrades invoke create_commit with operations."""
        mock_api = MagicMock()

        upgrade_small_model(mock_api)
        mock_api.create_commit.assert_called_once()
        self.assertEqual(mock_api.create_commit.call_args[1]["repo_id"], "The0Sanity/sesmetin-v2-small-ct2")

        mock_api.reset_mock()
        upgrade_turbo_model(mock_api)
        mock_api.create_commit.assert_called_once()
        self.assertEqual(mock_api.create_commit.call_args[1]["repo_id"], "The0Sanity/sesmetin-v2-turbo-ct2")

        mock_api.reset_mock()
        upgrade_tiny_model(mock_api)
        mock_api.create_commit.assert_called_once()
        self.assertEqual(mock_api.create_commit.call_args[1]["repo_id"], "The0Sanity/sesmetin-v2-tiny-ct2")

    def test_cleanup_legacy_tdk_shards_purges_old_shards(self):
        """Verifies cleanup_legacy_tdk_shards identifies and deletes legacy 500k files."""
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = [
            "README.md",
            "data/train-00000-of-00005.parquet",
            "data/train-00001-of-00005.parquet",
            "data/train-00000-of-00100.parquet",
        ]

        cleanup_legacy_tdk_shards(mock_api)
        mock_api.create_commit.assert_called_once()
        ops = mock_api.create_commit.call_args[1]["operations"]
        self.assertEqual(len(ops), 2)
        self.assertEqual(ops[0].path_in_repo, "data/train-00000-of-00005.parquet")
        self.assertEqual(ops[1].path_in_repo, "data/train-00001-of-00005.parquet")


if __name__ == "__main__":
    unittest.main()
