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

    def test_06_src_ui_canonical_imports_and_updater(self):
        """src.ui modülü ve otomatik güncelleme bileşenlerinin varlığını doğrular."""
        from src.config import APP_VERSION
        from src.ui.app import FletSpeechToTextApp
        from src.updater import AutoUpdater

        app = FletSpeechToTextApp()
        self.assertIsInstance(app.updater, AutoUpdater)
        self.assertEqual(app.APP_VERSION, APP_VERSION)
        self.assertTrue(callable(app.check_updates_dialog))
        self.assertTrue(callable(app.start_background_update_check))

        # Layout içinde Güncellemeleri Denetle butonu ve vX.X.X versiyon etiketi yer almalıdır
        layout = app.build_layout()
        found_update_btn = False
        found_version_label = False

        def _scan(ctrl):
            nonlocal found_update_btn, found_version_label
            if isinstance(ctrl, ft.FilledButton) and isinstance(ctrl.content, ft.Text):
                if "Güncelle" in (ctrl.content.value or ""):
                    found_update_btn = True
            if isinstance(ctrl, ft.Text) and f"v{APP_VERSION}" in (ctrl.value or ""):
                found_version_label = True
            if hasattr(ctrl, "controls") and isinstance(ctrl.controls, list):
                for child in ctrl.controls:
                    _scan(child)
            if hasattr(ctrl, "content") and ctrl.content is not None and isinstance(ctrl.content, ft.Control):
                _scan(ctrl.content)

        _scan(layout)
        self.assertTrue(found_update_btn, "Header içinde 'Güncellemeleri Denetle' butonu bulunmalıdır.")
        self.assertTrue(found_version_label, f"Header içinde 'v{APP_VERSION}' versiyon etiketi bulunmalıdır.")

    def test_07_button_hover_and_animation_attributes(self):
        """Butonların mikro-etkileşim ve ölçek animasyon özelliklerini doğrular."""
        from src.ui.app import FletSpeechToTextApp
        from src.ui.theme import ACCENT_LIGHT, ACCENT_PRIMARY

        app = FletSpeechToTextApp()
        self.assertIsNotNone(app.btn_start.animate_scale)
        self.assertIsNotNone(app.btn_cancel.animate_scale)
        self.assertTrue(callable(app._on_btn_start_hover))
        self.assertTrue(callable(app._on_btn_cancel_hover))

        # Hover simülasyonu: btn_start
        class MockHoverEvent:
            def __init__(self, data):
                self.data = data

        app._on_btn_start_hover(MockHoverEvent("true"))
        self.assertGreater(app.btn_start.scale, 1.0)
        self.assertEqual(app.btn_start.bgcolor, ACCENT_LIGHT)

        app._on_btn_start_hover(MockHoverEvent("false"))
        self.assertEqual(app.btn_start.scale, 1.0)
        self.assertEqual(app.btn_start.bgcolor, ACCENT_PRIMARY)

    def test_08_staggered_entrance_containers_and_animation(self):
        """Arayüz bölümlerinin kademeli açılış animasyonu özelliklerini doğrular."""
        import time
        from src.ui.app import FletSpeechToTextApp

        app = FletSpeechToTextApp()
        layout = app.build_layout()
        self.assertIsNotNone(layout)

        self.assertTrue(hasattr(app, "header_container"))
        self.assertTrue(hasattr(app, "left_column_container"))
        self.assertTrue(hasattr(app, "right_column_container"))

        self.assertIsNotNone(app.header_container.animate_opacity)
        self.assertIsNotNone(app.header_container.animate_offset)
        self.assertIsNotNone(app.left_column_container.animate_opacity)
        self.assertIsNotNone(app.right_column_container.animate_opacity)

        # Kademeli animasyonu calistir
        app.play_entrance_animation()
        for _ in range(30):
            if app.right_column_container.opacity == 1.0:
                break
            time.sleep(0.05)
        self.assertEqual(app.header_container.opacity, 1.0)
        self.assertEqual(app.left_column_container.opacity, 1.0)
        self.assertEqual(app.right_column_container.opacity, 1.0)


if __name__ == "__main__":
    unittest.main()

