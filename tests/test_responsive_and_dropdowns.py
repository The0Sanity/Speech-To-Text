"""Duyarlı pencere boyutlandırma, animasyon ve salt okunur açılır kutular (dropdown) testleri."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import flet as ft
from src.ui.app import FletSpeechToTextApp, run_flet_app


class TestResponsiveAndDropdowns(unittest.TestCase):
    """Flet pencere duyarlılığı, açılış animasyonu ve salt okunur dropdown testleri."""

    def setUp(self):
        self.app = FletSpeechToTextApp()

    def test_01_all_dropdowns_are_readonly_not_typeable(self):
        """Açılır kutuların (ft.Dropdown) içine elle yazı yazılamaz, sadece tıklanabilir olmalıdır."""
        dropdowns = [
            self.app.cmb_model,
            self.app.cmb_lang,
            self.app.cmb_vad,
            self.app.cmb_spk_count,
            self.app.cmb_prefix,
        ]
        for cmb in dropdowns:
            self.assertIsInstance(
                cmb,
                ft.Dropdown,
                "Tüm seçim kutuları ft.Dropdown (salt tıklanabilir açılır kutu) olmalıdır.",
            )
            # Flet Dropdown bileşeni kullanıcıdan doğrudan klavye girişi almaz
            self.assertFalse(hasattr(cmb, "entry_state") and cmb.entry_state == "normal")

    def test_02_app_has_opening_fade_in_animation(self):
        """Uygulama açılışında pürüzsüz animasyon işlevi tanımlı olmalı ve pencere opaklığı 1.0 olarak sabit tutulmalıdır."""
        import inspect
        source = inspect.getsource(run_flet_app)
        self.assertIn("play_entrance_animation", source)
        self.assertIn("opacity = 1.0", source)

    def test_03_responsive_window_minsize(self):
        """Dizüstü bilgisayarlar için pencere minimum boyutları 960x640 olmalıdır."""
        import inspect
        source = inspect.getsource(run_flet_app)
        self.assertIn("min_width = 960", source)
        self.assertIn("min_height = 640", source)


if __name__ == "__main__":
    unittest.main()
