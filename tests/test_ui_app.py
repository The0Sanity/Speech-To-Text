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
        self.assertEqual(self.app.updater.current_version, self.app.APP_VERSION)
        self.assertTrue(hasattr(self.app, "check_updates_dialog"))
        self.assertTrue(hasattr(self.app, "start_background_update_check"))

    def test_07_stepper_progression(self):
        """Adım göstergesinin durumu güncellemesi."""
        self.app.stepper.set_active_step(2)
        self.assertEqual(self.app.stepper.current_step, 2)
        self.app.stepper.reset()
        self.assertEqual(self.app.stepper.current_step, -1)

    def test_08_page_overlay_no_setter_bug_prevention(self):
        """Flet Page nesnesinin overlay özelliğinin setter'ı olmaması durumunda hata fırlatılmadığını doğrular."""
        class MockFletPageNoSetter:
            def __init__(self):
                self._overlay_list = []

            @property
            def overlay(self):
                return self._overlay_list

            def update(self):
                pass

        mock_page = MockFletPageNoSetter()
        self.app.page = mock_page

        # _show_toast çağrısı 'self.page.overlay = ...' yapmamalı, listeyi yerinde güncellemelidir
        try:
            self.app._show_toast("Test mesajı", is_error=False)
            self.assertEqual(len(mock_page.overlay), 1)
            # İkinci çağrıda eski SnackBar temizlenip yenisi eklenmeli
            self.app._show_toast("İkinci mesaj", is_error=True)
            self.assertEqual(len(mock_page.overlay), 1)
        except AttributeError as e:
            self.fail(f"_show_toast overlay setter hatası verdi: {e}")

    def test_09_model_hub_navigation_and_tab_switching(self):
        """Model Merkezi sekmesi ve Transkripsiyon sekmesi arası geçiş testi."""
        layout = self.app.build_layout()
        self.assertIsNotNone(layout)
        self.assertTrue(self.app.transcription_view.visible)
        self.assertFalse(self.app.model_hub_view.visible)

        # Model Merkezi sekmesine geçiş
        self.app._switch_nav_tab("model_hub")
        self.assertFalse(self.app.transcription_view.visible)
        self.assertTrue(self.app.model_hub_view.visible)

        # Transkripsiyon sekmesine geri dönüş
        self.app._switch_nav_tab("transcription")
        self.assertTrue(self.app.transcription_view.visible)
        self.assertFalse(self.app.model_hub_view.visible)

    def test_10_model_hub_refresh_and_cards_population(self):
        """Model Merkezi kartlarının doğru şekilde doldurulduğunu doğrula."""
        self.app.build_layout()
        self.app.refresh_model_hub()
        # Kartlar sütununda hem SesMetin hem de resmi modeller bulunmalı
        self.assertGreater(len(self.app.model_cards_column.controls), 5)

    def test_11_model_hub_set_default_model(self):
        """Model Merkezi üzerinden varsayılan model değiştirildiğinde dropdown ve ayarların güncellenmesi."""
        self.app.build_layout()
        self.app._set_default_model("sesmetin-v1-turbo")
        self.assertIn("sesmetin-v1-turbo", self.app.cmb_model.value.lower())
        self.assertEqual(self.app.settings.get("model_size"), "sesmetin-v1-turbo")


if __name__ == "__main__":
    unittest.main()

