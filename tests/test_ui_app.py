"""Arayüz (App) bileşen ve kullanıcı akışı entegrasyon testleri."""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ui.app import SpeechToTextApp


class TestAppIntegration(unittest.TestCase):
    """Ana GUI penceresi durum ve fonksiyon testleri."""

    @classmethod
    def setUpClass(cls):
        # GUI'yi pencereyi ekranda göstermeden (withdraw) oluştur
        cls.app = SpeechToTextApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def test_01_app_initialization(self):
        """Pencerenin ve bileşenlerinin doğru ilklendirildiğini doğrula."""
        self.assertIsNotNone(self.app.main_container)
        self.assertIsNotNone(self.app.stepper)
        self.assertIsNotNone(self.app.audio_player)
        self.assertIsNotNone(self.app.search_entry)
        self.assertIsNotNone(self.app.btn_start)
        self.assertIsNotNone(self.app.badge_duration)

    def test_02_render_transcript_and_metrics(self):
        """Transkript çizimi ve metrik kartlarının güncellenmesi testi."""
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 3.0, "text": "Merhabalar", "timestamp_display": "[00:00 - 00:03]"},
            {"id": 2, "speaker": "X2", "start": 3.5, "end": 7.0, "text": "Hoş geldiniz projemize.", "timestamp_display": "[00:03 - 00:07]"},
        ]
        self.app.transcribed_data = mock_data
        self.app._render_transcript(mock_data)

        self.assertEqual(self.app.lbl_total_turns.cget("text"), "2 konuşma parçası")
        self.assertIn("2 Kişi", self.app.badge_speakers.lbl_val.cget("text"))

    def test_03_filter_transcript(self):
        """Canlı arama filtresinin uygulanması."""
        self.app.search_entry.delete(0, "end")
        self.app.search_entry.insert(0, "projemize")
        self.app._filter_transcript()

        self.assertIn("1 / 2 eşleşme", self.app.lbl_search_count.cget("text"))

        # Aramayı temizle
        self.app.search_entry.delete(0, "end")
        self.app._filter_transcript()
        self.assertEqual(self.app.lbl_search_count.cget("text"), "")

    def test_04_find_and_replace_action(self):
        """Bul ve değiştir eyleminin arayüz üzerinden işletilmesi."""
        self.app.entry_find.delete(0, "end")
        self.app.entry_find.insert(0, "Merhabalar")
        self.app.entry_replace.delete(0, "end")
        self.app.entry_replace.insert(0, "Selamlar")

        self.app._execute_find_replace()
        self.assertEqual(self.app.transcribed_data[0]["text"], "Selamlar")

    def test_05_speaker_rename_action(self):
        """Konuşmacı yeniden adlandırmasının arayüz üzerinden işletilmesi."""
        self.app._apply_speaker_rename("X1", "Sunucu")
        self.assertEqual(self.app.transcribed_data[0]["speaker"], "Sunucu")

    def test_06_theme_toggle(self):
        """Koyu ve Açık tema geçişi testi."""
        orig_theme = self.app.current_theme
        self.app._toggle_theme()
        new_theme = self.app.current_theme
        self.assertNotEqual(orig_theme, new_theme)

        # Eski temaya geri döndür
        self.app._toggle_theme()
        self.assertEqual(self.app.current_theme, orig_theme)

    def test_07_stepper_progression(self):
        """Adım göstergesinin durumu güncellemesi."""
        self.app.stepper.set_active_step(2)
        badge_2 = self.app.stepper.step_labels[2]
        self.assertEqual(badge_2.cget("text_color"), "#60a5fa")
        self.app.stepper.reset()


if __name__ == "__main__":
    unittest.main()
