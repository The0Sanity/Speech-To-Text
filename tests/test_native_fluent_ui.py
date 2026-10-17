"""Windows Native Fluent Design ve Arayüz Görsel Standartları Testleri."""

import os
import re
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestNativeFluentUI(unittest.TestCase):
    """Masaüstü ve dizüstü sistemlerde yerel Windows Fluent arayüz standartlarını doğrular."""

    def test_01_main_has_windows_high_dpi_awareness(self):
        """main.py dosyasında yüksek DPI ekranlar (laptop 125%/150%) için Windows DPI ölçekleme desteği olmalıdır."""
        main_file = BASE_DIR / "main.py"
        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Windows DPI awareness API çağrısı aranır
        has_dpi = (
            "SetProcessDpiAwareness" in content
            or "SetProcessDpiAwarenessContext" in content
            or "shcore" in content
        )
        self.assertTrue(has_dpi, "main.py Windows High-DPI (SetProcessDpiAwareness/shcore) desteği içermelidir.")

    def test_02_fluent_font_family_configured(self):
        """style.py içinde yerel Windows Segoe UI / Segoe UI Variable font ailesi tanımlı olmalıdır."""
        style_file = BASE_DIR / "src" / "ui" / "style.py"
        with open(style_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Segoe UI", content, "style.py yerel 'Segoe UI' sistem yazı tipini barındırmalıdır.")

    def test_03_fluent_theme_palette_harmony(self):
        """style.py içinde Windows 11 Fluent renk paleti tanımlı olmalıdır."""
        from src.ui.style import THEME_PALETTES

        self.assertIn("dark", THEME_PALETTES)
        dark = THEME_PALETTES["dark"]

        # Fluent Dark tonları: #202020 civarı zemin ve #2b2b2b / #323232 kartlar
        self.assertIn("bg_main", dark)
        self.assertIn("bg_card", dark)
        self.assertIn("border_card", dark)

        # Arka plan aşırı sert zifiri siyah (#000000 veya #0b0f17) yerine Fluent Dark dengeli tonunda olmalı
        self.assertNotEqual(dark["bg_main"], "#0b0f17", "bg_main Fluent Dark (#202020) tonuna güncellenmelidir.")

    def test_04_stepper_has_all_five_numbered_steps(self):
        """ProcessStepper bileşeninin 5 adımı da eksiksiz numaralandırılmış olmalıdır."""
        from src.ui.components import ProcessStepper

        steps = ProcessStepper.STEPS
        self.assertEqual(len(steps), 5, "Stepper tam 5 aşamadan oluşmalıdır.")
        for idx, (code, label) in enumerate(steps, start=1):
            self.assertTrue(
                label.startswith(f"{idx}."),
                f"Adım etiketi '{idx}.' ile başlamalıdır: {label}",
            )

    def test_05_export_buttons_use_unified_fluent_styling(self):
        """app.py dışa aktarma butonları gökkuşağı rengi yerine yeknesak Fluent nötr buton stili kullanmalıdır."""
        app_file = BASE_DIR / "src" / "ui" / "app.py"
        with open(app_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Eski gökkuşağı renk kodlarının (#0369a1, #6366f1, #059669, #0f766e) butonlarda bulunmaması gerekir
        rainbow_colors = ["#0369a1", "#6366f1", "#059669", "#0f766e"]
        for color in rainbow_colors:
            self.assertNotIn(
                color,
                content,
                f"Dışa aktarma butonlarında dağınık gökkuşağı rengi ({color}) yerine yeknesak Fluent stili kullanılmalıdır.",
            )


if __name__ == "__main__":
    unittest.main()
