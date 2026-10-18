"""Unit tests for Prtk model evaluation metrics (WER, CER) and benchmark reporting."""

import unittest
from typing import List


def compute_wer(reference: str, hypothesis: str) -> float:
    """Computes Word Error Rate (WER) between reference and hypothesis text."""
    ref_words = reference.strip().lower().split()
    hyp_words = hypothesis.strip().lower().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Levenshtein distance on words
    r_len, h_len = len(ref_words), len(hyp_words)
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[r_len][h_len] / r_len


def compute_cer(reference: str, hypothesis: str) -> float:
    """Computes Character Error Rate (CER) between reference and hypothesis text."""
    ref_chars = list(reference.strip().lower().replace(" ", ""))
    hyp_chars = list(hypothesis.strip().lower().replace(" ", ""))
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    r_len, h_len = len(ref_chars), len(hyp_chars)
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[r_len][h_len] / r_len


class TestPrtkModelEvaluation(unittest.TestCase):
    """Test suite for evaluation metrics and accuracy benchmarking."""

    def test_01_compute_wer_exact_match(self):
        ref = "bir patates iki patates uc patates"
        hyp = "bir patates iki patates uc patates"
        self.assertEqual(compute_wer(ref, hyp), 0.0)

    def test_02_compute_wer_with_substitution_and_deletion(self):
        ref = "kediler tombik tombik"
        hyp = "kediler tombi"
        wer = compute_wer(ref, hyp)
        self.assertGreater(wer, 0.0)
        self.assertLessEqual(wer, 1.0)

    def test_03_compute_cer(self):
        ref = "patates"
        hyp = "patatas"
        cer = compute_cer(ref, hyp)
        self.assertAlmostEqual(cer, 1.0 / 7.0, places=4)

    def test_04_compute_wer_empty_strings(self):
        self.assertEqual(compute_wer("", ""), 0.0)
        self.assertEqual(compute_wer("hello", ""), 1.0)


if __name__ == "__main__":
    unittest.main()
