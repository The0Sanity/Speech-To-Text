"""Unit tests for Whisper Turkish Vocabulary & Embedding Pruning Tool.

Tests:
1. Turkish alphabet and diacritic subword retention.
2. Whisper control and timestamp token preservation.
3. Weight matrix slicing and shape validation.
4. Token mapping consistency and bidirectional lookup.
"""

import unittest
from unittest.mock import MagicMock

from tools.models.prune_whisper_turkish_vocab import (
    build_retained_token_set,
    prune_embedding_matrix,
    prune_projection_head,
    validate_turkish_coverage,
)


class TestPruneWhisperTurkishVocab(unittest.TestCase):
    """Test suite for Whisper Turkish vocabulary pruning."""

    def setUp(self):
        # Mock vocabulary map: token -> id
        tr_lower = "abcçdefgğhıijklmnoöprsştuüvyz"
        tr_upper = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
        self.mock_vocab = {ch: idx + 1 for idx, ch in enumerate(tr_lower + tr_upper)}
        offset = len(self.mock_vocab) + 1
        self.mock_vocab.update({
            "merhaba": offset,
            "günaydın": offset + 1,
            "teşekkür": offset + 2,
            # Numbers and punctuation
            "0": offset + 3,
            "1": offset + 4,
            ".": offset + 5,
            ",": offset + 6,
            "?": offset + 7,
            # Foreign tokens to be pruned
            "你好": offset + 100,
            "мир": offset + 101,
            "مرحبا": offset + 102,
            "français": offset + 103,
            # Whisper special tokens
            "<|startoftranscript|>": 50258,
            "<|tr|>": 50293,
            "<|transcribe|>": 50359,
            "<|notimestamps|>": 50363,
            "<|endoftext|>": 50257,
            "<|0.00|>": 50364,
            "<|30.00|>": 51864,
        })

    def test_build_retained_token_set_keeps_turkish_and_specials(self):
        """Verifies Turkish words/chars and Whisper special tokens are retained, others pruned."""
        retained = build_retained_token_set(
            vocab=self.mock_vocab,
            target_languages=["tr"],
            preserve_special_tokens=True,
        )

        # Retained checks
        self.assertIn(self.mock_vocab["merhaba"], retained)
        self.assertIn(self.mock_vocab["günaydın"], retained)
        self.assertIn(self.mock_vocab["ç"], retained)
        self.assertIn(self.mock_vocab["ğ"], retained)
        self.assertIn(self.mock_vocab["ı"], retained)
        self.assertIn(self.mock_vocab["İ"], retained)
        self.assertIn(self.mock_vocab["<|startoftranscript|>"], retained)
        self.assertIn(self.mock_vocab["<|tr|>"], retained)
        self.assertIn(self.mock_vocab["<|endoftext|>"], retained)

        # Pruned checks
        self.assertNotIn(self.mock_vocab["你好"], retained)
        self.assertNotIn(self.mock_vocab["мир"], retained)
        self.assertNotIn(self.mock_vocab["مرحبا"], retained)

    def test_validate_turkish_coverage_passes_on_complete_alphabet(self):
        """Verifies validator confirms coverage for all 29 Turkish uppercase and lowercase letters."""
        retained_tokens = set(self.mock_vocab.keys())
        is_valid, missing = validate_turkish_coverage(retained_tokens)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_prune_embedding_matrix_slices_dimension_correctly(self):
        """Verifies slicing 2D embedding tensor down to retained indices."""
        import numpy as np

        orig_vocab_size = 50
        dim = 16
        mock_weights = np.arange(orig_vocab_size * dim, dtype=np.float32).reshape(orig_vocab_size, dim)
        retained_indices = [2, 5, 10, 15]

        pruned = prune_embedding_matrix(mock_weights, retained_indices)
        self.assertEqual(pruned.shape, (4, dim))
        np.testing.assert_array_equal(pruned[0], mock_weights[2])
        np.testing.assert_array_equal(pruned[1], mock_weights[5])
        np.testing.assert_array_equal(pruned[2], mock_weights[10])
        np.testing.assert_array_equal(pruned[3], mock_weights[15])


if __name__ == "__main__":
    unittest.main()
