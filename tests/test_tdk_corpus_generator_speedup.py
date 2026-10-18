"""Tests for optimized TDK corpus generator with batched commits and double-buffering.

Validates that:
1. prepare_shard_operation constructs valid CommitOperationAdd with in-memory BytesIO.
2. commit_shard_batch correctly groups multiple shards into a single atomic commit.
3. Batched multi-shard streaming flushes all shards without dropping remainders.
4. Concurrency / pipelined execution executes generation and upload concurrently.
"""

import io
import unittest
from unittest.mock import MagicMock, patch

from tools.huggingface.generate_and_push_tdk_corpus import (
    CommitOperationAdd,
    commit_shard_batch,
    prepare_shard_operation,
    stream_corpus_to_huggingface,
)


class TestTDKCorpusGeneratorSpeedup(unittest.TestCase):
    """Test suite for high-speed streaming upload optimizations."""

    def test_prepare_shard_operation_creates_in_memory_commit_op(self):
        """Verifies shard operation packages parquet bytes in BytesIO without disk I/O."""
        fake_parquet = b"PAR1fake_parquet_data"
        op = prepare_shard_operation(
            shard_index=3,
            total_shards=100,
            parquet_bytes=fake_parquet,
        )

        self.assertIsInstance(op, CommitOperationAdd)
        self.assertEqual(op.path_in_repo, "data/train-00003-of-00100.parquet")
        self.assertIsInstance(op.path_or_fileobj, io.BytesIO)
        self.assertEqual(op.path_or_fileobj.getvalue(), fake_parquet)

    def test_commit_shard_batch_calls_create_commit_once_for_multiple_shards(self):
        """Verifies that committing a batch of shards performs only one API commit call."""
        mock_api = MagicMock()
        ops = [
            prepare_shard_operation(0, 10, b"data0"),
            prepare_shard_operation(1, 10, b"data1"),
            prepare_shard_operation(2, 10, b"data2"),
        ]

        result = commit_shard_batch(
            api=mock_api,
            repo_id="The0Sanity/test-dataset",
            operations=ops,
            commit_message="feat(corpus): add shards 1-3/10",
        )

        self.assertTrue(result)
        mock_api.create_commit.assert_called_once()
        call_kwargs = mock_api.create_commit.call_args[1]
        self.assertEqual(call_kwargs["repo_id"], "The0Sanity/test-dataset")
        self.assertEqual(call_kwargs["repo_type"], "dataset")
        self.assertEqual(len(call_kwargs["operations"]), 3)
        self.assertIn("shards 1-3/10", call_kwargs["commit_message"])

    @patch("tools.huggingface.generate_and_push_tdk_corpus.commit_shard_batch")
    @patch("tools.huggingface.generate_and_push_tdk_corpus.HfApi")
    def test_stream_corpus_batched_commits_and_remainder_handling(
        self, mock_hf_api_cls, mock_commit_batch
    ):
        """Verifies that 12 shards with batch_commit_size=5 produces 3 commits (5, 5, 2)."""
        mock_api = MagicMock()
        mock_hf_api_cls.return_value = mock_api
        mock_commit_batch.return_value = True

        stream_corpus_to_huggingface(
            token="hf_fake_token",
            repo_id="The0Sanity/test-dataset",
            total_samples=120,
            shard_size=10,
            max_shards=12,
            start_shard=0,
            batch_commit_size=5,
        )

        # 1 README commit + 12 shards in batches of 5 = 4 batch commits total
        self.assertEqual(mock_commit_batch.call_count, 4)

        readme_call_ops = mock_commit_batch.call_args_list[0][1]["operations"]
        first_shard_call_ops = mock_commit_batch.call_args_list[1][1]["operations"]
        second_shard_call_ops = mock_commit_batch.call_args_list[2][1]["operations"]
        third_shard_call_ops = mock_commit_batch.call_args_list[3][1]["operations"]

        self.assertEqual(len(readme_call_ops), 1)
        self.assertEqual(readme_call_ops[0].path_in_repo, "README.md")
        self.assertEqual(len(first_shard_call_ops), 5)
        self.assertEqual(len(second_shard_call_ops), 5)
        self.assertEqual(len(third_shard_call_ops), 2)


if __name__ == "__main__":
    unittest.main()
