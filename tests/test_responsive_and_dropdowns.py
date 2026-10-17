"""Duyarlı pencere boyutlandırma, animasyon ve salt okunur açılır kutular (dropdown) testleri."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import customtkinter as ctk
from src.ui.app import SpeechToTextApp


class TestResponsiveAndDropdowns(unittest.TestCase):
    """Pencere yeniden boyutlandırma, açılış animasyonu ve salt okunur dropdown testleri."""

    @classmethod
    def setUpClass(cls):
        ctk.set_appearance_mode("Dark")
        cls.app = SpeechToTextApp()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def test_01_all_dropdowns_are_readonly_not_typeable(self):
        """Açılır kutuların (ComboBox) içine elle yazı yazılamamalı, sadece tıklanabilir (readonly) olmalıdır."""
        dropdowns = [
            self.app.cmb_model,
            self.app.cmb_lang,
            self.app.cmb_vad,
            self.app.cmb_spk_count,
            self.app.cmb_prefix,
        ]
        for cmb in dropdowns:
            state = cmb.cget("state")
            self.assertEqual(
                state,
                "readonly",
                f"Açılır kutu state='readonly' olmalıdır ancak '{state}' bulundu. Elle yazım engellenmelidir.",
            )

    def test_02_app_has_opening_fade_in_animation(self):
        """Uygulama açılışında pürüzsüz animasyon metodu tanımlı olmalıdır."""
        self.assertTrue(
            hasattr(self.app, "_animate_window_entrance"),
            "SpeechToTextApp sınıfında '_animate_window_entrance' animasyon metodu bulunmalıdır.",
        )

    def test_03_responsive_window_minsize(self):
        """Dizüstü bilgisayarlar (1366x768 / 1080p %150 ölçek) için minsize <= 960x640 olmalıdır."""
        min_w = getattr(self.app, "_min_width", 1000)
        min_h = getattr(self.app, "_min_height", 720)
        self.assertLessEqual(min_w, 960, f"Pencere min_w ({min_w}) 960 veya daha küçük olmalıdır.")
        self.assertLessEqual(min_h, 640, f"Pencere min_h ({min_h}) 640 veya daha küçük olmalıdır.")


if __name__ == "__main__":
    unittest.main()
