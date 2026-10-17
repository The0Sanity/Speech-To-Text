"""Flet Arayüz (App) bileşen ve kullanıcı akışı entegrasyon testleri."""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ui.app import FletSpeechToTextApp


class TestAppIntegration(unittest.TestCase):
    """Ana Flet masaüstü penceresi durum ve fonksiyon testleri."""

    def setUp(self):
        self.app = FletSpeechToTextApp()

    def test_01_app_initialization(self):
        """Pencerenin ve bileşenlerinin doğru ilklendirildiğini doğrula."""
        self.assertIsNotNone(self.app.stepper)
        self.assertIsNotNone(self.app.audio_player)
        self.assertIsNotNone(self.app.search_entry)
        self.assertIsNotNone(self.app.btn_start)
        self.assertIsNotNone(self.app.badge_duration)
        self.assertIsNotNone(self.app.updater)

    def test_02_render_transcript_and_metrics(self):
        """Transkript çizimi ve metrik kartlarının güncellenmesi testi."""
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 3.0, "text": "Merhabalar"},
            {"id": 2, "speaker": "X2", "start": 3.5, "end": 7.0, "text": "Hoş geldiniz projemize."},
        ]
        self.app.set_transcribed_data(mock_data)
        self.assertEqual(len(self.app.transcribed_data), 2)
        self.assertIn("2 Kişi", self.app.badge_speakers.lbl_val.value)

    def test_03_filter_transcript(self):
        """Canlı arama filtresinin uygulanması."""
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 3.0, "text": "Merhabalar"},
            {"id": 2, "speaker": "X2", "start": 3.5, "end": 7.0, "text": "Hoş geldiniz projemize."},
        ]
        self.app.set_transcribed_data(mock_data)
        self.app.search_entry.value = "projemize"
        self.app.on_search_change(None)
        self.assertIn("1 / 2", self.app.lbl_search_count.value)

        # Aramayı temizle
        self.app.search_entry.value = ""
        self.app.on_search_change(None)
        self.assertEqual(self.app.lbl_search_count.value, "")

    def test_04_find_and_replace_action(self):
        """Bul ve değiştir eyleminin arayüz üzerinden işletilmesi."""
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 3.0, "text": "Merhabalar"},
        ]
        self.app.set_transcribed_data(mock_data)
        self.app.entry_find.value = "Merhabalar"
        self.app.entry_replace.value = "Selamlar"
        self.app.execute_find_replace()
        self.assertEqual(self.app.transcribed_data[0]["text"], "Selamlar")

    def test_05_speaker_rename_action(self):
        """Konuşmacı yeniden adlandırmasının arayüz üzerinden işletilmesi."""
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 3.0, "text": "Merhabalar"},
        ]
        self.app.set_transcribed_data(mock_data)
        self.app.apply_speaker_rename("X1", "Sunucu")
        self.assertEqual(self.app.transcribed_data[0]["speaker"], "Sunucu")

    def test_06_updater_integration(self):
        """AutoUpdater bileşeninin uygulamaya doğru şekilde bağlandığını doğrular."""
        self.assertEqual(self.app.updater.current_version, "1.0.0")
        self.assertTrue(hasattr(self.app, "check_updates_dialog"))
        self.assertTrue(hasattr(self.app, "start_background_update_check"))

    def test_07_stepper_progression(self):
        """Adım göstergesinin durumu güncellemesi."""
        self.app.stepper.set_active_step(2)
        self.assertEqual(self.app.stepper.current_step, 2)
        self.app.stepper.reset()
        self.assertEqual(self.app.stepper.current_step, -1)


if __name__ == "__main__":
    unittest.main()
