"""Flet kullanıcı arayüzü, bileşenleri, tema ve kullanıcı akışı testleri (Test-First)."""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import flet as ft


class TestFletUI(unittest.TestCase):
    """Flet tabanlı modern yerel masaüstü arayüzü birim ve yapı testleri."""

    def test_01_flet_theme_and_colors(self):
        """src/ui_flet/theme.py renk paleti ve konuşmacı renk haritalaması."""
        from src.ui_flet.theme import (
            BG_APP,
            BG_CARD,
            ACCENT_PRIMARY,
            BORDER_CARD,
            get_speaker_color,
        )

        self.assertIsNotNone(BG_APP)
        self.assertIsNotNone(BG_CARD)
        self.assertIsNotNone(ACCENT_PRIMARY)
        self.assertIsNotNone(BORDER_CARD)

        # Konuşmacı renk fonksiyonu geçerli hex kodu dönmelidir
        c1 = get_speaker_color("X1")
        c2 = get_speaker_color("X2")
        self.assertTrue(c1.startswith("#"))
        self.assertTrue(c2.startswith("#"))
        self.assertNotEqual(c1, c2)

    def test_02_stepper_has_five_numbered_steps(self):
        """ProcessStepper bileşeni tam 5 adımı barındırmalı ve numaralı olmalıdır."""
        from src.ui_flet.components import ProcessStepper

        stepper = ProcessStepper()
        self.assertEqual(len(stepper.STEPS), 5)
        for idx, (code, label) in enumerate(stepper.STEPS, start=1):
            self.assertTrue(label.startswith(f"{idx}."))

        # Aktif adımı değiştirme fonksiyonu
        stepper.set_active_step(2)
        self.assertEqual(stepper.current_step, 2)

    def test_03_metric_card(self):
        """MetricCard bileşeni başlık ve değer gösterimini doğru yönetmelidir."""
        from src.ui_flet.components import MetricCard

        card = MetricCard(title="Süre", value="00:00")
        self.assertEqual(card.lbl_title.value, "SÜRE")
        self.assertEqual(card.lbl_val.value, "00:00")

        card.update_value("05:32")
        self.assertEqual(card.lbl_val.value, "05:32")

    def test_04_app_structure_and_dropdowns_readonly(self):
        """FletSpeechToTextApp sınıfının açılır menüleri (Dropdown) ve bileşenleri eksiksiz olmalıdır."""
        from src.ui_flet.app import FletSpeechToTextApp

        app = FletSpeechToTextApp()

        # 5 Temel Açılır Kutu (Dropdown)
        dropdowns = [
            app.cmb_model,
            app.cmb_lang,
            app.cmb_vad,
            app.cmb_spk_count,
            app.cmb_prefix,
        ]
        for cmb in dropdowns:
            self.assertIsInstance(cmb, ft.Dropdown, "Açılır kutu ft.Dropdown olmalıdır.")
            self.assertTrue(len(cmb.options) > 0, "Açılır kutu seçenekleri dolu olmalıdır.")

        # Temel butonlar ve göstergeler
        self.assertIsNotNone(app.btn_start)
        self.assertIsNotNone(app.btn_cancel)
        self.assertIsNotNone(app.progress_bar)
        self.assertIsNotNone(app.stepper)
        self.assertIsNotNone(app.audio_player)
        self.assertIsNotNone(app.search_entry)
        self.assertIsNotNone(app.badge_duration)
        self.assertIsNotNone(app.badge_speakers)
        self.assertIsNotNone(app.badge_words)
        self.assertIsNotNone(app.badge_wpm)

    def test_05_render_transcript_and_find_replace(self):
        """Transkript listesi çizimi ve Bul & Değiştir mantığı."""
        from src.ui_flet.app import FletSpeechToTextApp

        app = FletSpeechToTextApp()
        mock_data = [
            {"id": 1, "speaker": "X1", "start": 0.0, "end": 2.5, "text": "Merhabalar efendim."},
            {"id": 2, "speaker": "X2", "start": 2.8, "end": 5.0, "text": "Toplantıya hoş geldiniz."},
        ]

        app.set_transcribed_data(mock_data)
        self.assertEqual(len(app.transcribed_data), 2)
        self.assertEqual(app.badge_speakers.lbl_val.value, "2 Kişi")

        # Bul ve Değiştir testi
        app.entry_find.value = "efendim"
        app.entry_replace.value = "arkadaşlar"
        replaced_count = app.execute_find_replace()
        self.assertEqual(replaced_count, 1)
        self.assertIn("arkadaşlar", app.transcribed_data[0]["text"])


if __name__ == "__main__":
    unittest.main()
