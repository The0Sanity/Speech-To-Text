"""Unit tests for TDK Language Model rescoring and phonetic Levenshtein snapping."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.language_model import TDKLanguageModelRescorer


class TestTDKLanguageModelRescorer(unittest.TestCase):
    """Test suite for TDK n-gram and phonetic snapping engine."""

    @classmethod
    def setUpClass(cls):
        cls.rescorer = TDKLanguageModelRescorer()

    def test_01_valid_turkish_scores_higher_than_gibberish(self):
        """Natural Turkish sentence should receive a higher language model log-probability."""
        valid_sentence = "bir patates iki domates üç portakal"
        gibberish_sentence = "xyz qqq wwww jjjj zzz"

        score_valid = self.rescorer.score_sentence(valid_sentence)
        score_gibberish = self.rescorer.score_sentence(gibberish_sentence)

        self.assertGreater(score_valid, score_gibberish)

    def test_02_phonetic_snap_corrects_near_misses(self):
        """Acoustic near-misses of Turkish words should snap to valid TDK words."""
        # e.g., 'pazates' -> 'patates', 'domatez' -> 'domates'
        snapped_potato = self.rescorer.snap_word("pazates")
        self.assertEqual(snapped_potato, "patates")

        snapped_tomato = self.rescorer.snap_word("domatez")
        self.assertEqual(snapped_tomato, "domates")

    def test_03_preserves_proper_nouns_and_valid_words(self):
        """Proper nouns and words that are not phonetically ambiguous should remain untouched."""
        valid_word = "bilgisayar"
        self.assertEqual(self.rescorer.snap_word(valid_word), valid_word)

        tech_word = "GitHub"
        self.assertEqual(self.rescorer.snap_word(tech_word), tech_word)

    def test_04_beam_rescoring_selects_correct_candidate(self):
        """Given candidate beam hypotheses, the rescorer should rank the grammatically valid hypothesis first."""
        hypotheses = [
            {"text": "1 pazates pazates", "acoustic_score": -2.1},
            {"text": "1 patates patates", "acoustic_score": -2.3},  # Slightly lower acoustic confidence but genuine words
        ]

        rescored = self.rescorer.rescore_hypotheses(hypotheses, lm_weight=0.5)
        self.assertEqual(rescored[0]["text"], "1 patates patates")


if __name__ == "__main__":
    unittest.main()
