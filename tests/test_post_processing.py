"""Unit tests for Turkish phonetic post-processing and Inverse Text Normalization (ITN).

Verifies numeral formatting, currency and percentage resolution, phonetic ambiguity
correction, and morphological text consistency in SesMetin Pro.
"""

import unittest
from src.transcription.post_processing import (
    TurkishITNProcessor,
    TurkishPhoneticCorrector,
    post_process_transcript
)


class TestTurkishPostProcessing(unittest.TestCase):
    """Test suite for Turkish ITN and phonetic post-processing."""

    def setUp(self):
        self.itn = TurkishITNProcessor()
        self.corrector = TurkishPhoneticCorrector()

    def test_number_normalization_simple(self):
        """Verify spoken numbers are normalized to standard digits."""
        text = "bu sistem tam on bes saniye icinde calisir"
        normalized = self.itn.normalize_numbers(text)
        self.assertIn("15", normalized)

    def test_number_normalization_large(self):
        """Verify large Turkish numbers such as yüz bin, bir milyon."""
        text = "toplam yuz bin test uygulandi"
        normalized = self.itn.normalize_numbers(text)
        self.assertIn("100.000", normalized)

        text2 = "bir milyon iki yuz bin kullanici"
        normalized2 = self.itn.normalize_numbers(text2)
        self.assertIn("1.200.000", normalized2)

    def test_percentage_normalization(self):
        """Verify percentages such as 'yüzde sıfır nokta bir' convert to '%0.1'."""
        text = "hata orani yuzde sifir nokta bir seviyesine indi"
        normalized = self.itn.normalize_percentages(text)
        self.assertIn("%0.1", normalized)

        text2 = "yuzde elli basari"
        normalized2 = self.itn.normalize_percentages(text2)
        self.assertIn("%50", normalized2)

    def test_currency_normalization(self):
        """Verify Turkish Lira and major currencies are formatted correctly."""
        text = "toplam maliyet kirk bes lira oldu"
        normalized = self.itn.normalize_currencies(text)
        self.assertIn("45 TL", normalized)

        text2 = "yuz dolar odeme alindi"
        normalized2 = self.itn.normalize_currencies(text2)
        self.assertIn("100 USD", normalized2)

    def test_phonetic_error_correction(self):
        """Verify common acoustic and phonetic transcription artifacts are corrected."""
        text = "ses metin pro modeli yuksek dogruluk saglar"
        corrected = self.corrector.correct_phonetic_confusions(text)
        self.assertIn("SesMetin Pro", corrected)

        text2 = "yapa zeka algoritmasi"
        corrected2 = self.corrector.correct_phonetic_confusions(text2)
        self.assertIn("yapay zeka", corrected2)

    def test_colloquial_preservation(self):
        """Verify colloquial phrases are not distorted into improper numbers."""
        text = "oraya uc bes kisi geldi"
        processed = post_process_transcript(text)
        self.assertIn("üç beş kişi", processed)

    def test_end_to_end_post_processing(self):
        """Verify full pipeline produces clean, standard Turkish formatting."""
        raw = "ses metin pro yuz bin test uzerinde yuzde sifir nokta bir hata verdi"
        result = post_process_transcript(raw)
        self.assertIn("SesMetin Pro", result)
        self.assertIn("100.000", result)
        self.assertIn("%0.1", result)


if __name__ == "__main__":
    unittest.main()
