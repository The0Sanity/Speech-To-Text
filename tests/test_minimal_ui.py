"""Minimalist arayüz ve emoji kontrolü birim testleri."""

import os
import re
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Emoji aralığı regex kalıbı (Standart emojiler ve semboller)
EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff]"  # SMP emojileri
    r"|[\u2600-\u27bf]"          # Çeşitli semboller ve Dingbats
    r"|[\u2300-\u23ff]"          # Çeşitli teknik semboller (▶, ⏸, vb.)
)


class TestMinimalistUI(unittest.TestCase):
    """UI dosyalarında emoji bulunmadığını ve run.bat'ın otomatik kontrol mantığını doğrular."""

    def test_01_no_emojis_in_ui_components(self):
        """src/ui/components.py dosyasında kullanıcıya görünen hiçbir emoji olmamalıdır."""
        comp_file = BASE_DIR / "src" / "ui" / "components.py"
        with open(comp_file, "r", encoding="utf-8") as f:
            content = f.read()

        emojis_found = EMOJI_PATTERN.findall(content)
        self.assertEqual(
            len(emojis_found),
            0,
            f"components.py içinde istenmeyen emojiler tespit edildi: {set(emojis_found)}",
        )

    def test_02_no_emojis_in_ui_app(self):
        """src/ui/app.py dosyasında kullanıcıya görünen hiçbir emoji olmamalıdır."""
        app_file = BASE_DIR / "src" / "ui" / "app.py"
        with open(app_file, "r", encoding="utf-8") as f:
            content = f.read()

        emojis_found = EMOJI_PATTERN.findall(content)
        self.assertEqual(
            len(emojis_found),
            0,
            f"app.py içinde istenmeyen emojiler tespit edildi: {set(emojis_found)}",
        )

    def test_03_no_emojis_in_exporters(self):
        """src/exporter.py dosyasında hiçbir emoji olmamalıdır."""
        exp_file = BASE_DIR / "src" / "exporter.py"
        with open(exp_file, "r", encoding="utf-8") as f:
            content = f.read()

        emojis_found = EMOJI_PATTERN.findall(content)
        self.assertEqual(
            len(emojis_found),
            0,
            f"exporter.py içinde istenmeyen emojiler tespit edildi: {set(emojis_found)}",
        )

    def test_04_run_bat_has_automated_dependency_check(self):
        """run.bat dosyasının bağımlılık kontrolü ve otomatik kurulum mantığı içermesi."""
        bat_file = BASE_DIR / "run.bat"
        self.assertTrue(bat_file.exists(), "run.bat dosyası mevcut olmalıdır.")

        with open(bat_file, "r", encoding="utf-8", errors="ignore") as f:
            bat_content = f.read()

        # Bağımlılık kontrolü ve otomatik çalıştırma içermeli
        self.assertIn("customtkinter", bat_content)
        self.assertIn("requirements.txt", bat_content)
        self.assertIn("main.py", bat_content)

    def test_05_no_emojis_in_readme(self):
        """README.md dosyasında hiçbir emoji olmamalıdır."""
        readme_file = BASE_DIR / "README.md"
        with open(readme_file, "r", encoding="utf-8") as f:
            content = f.read()

        emojis_found = EMOJI_PATTERN.findall(content)
        self.assertEqual(
            len(emojis_found),
            0,
            f"README.md içinde istenmeyen emojiler tespit edildi: {set(emojis_found)}",
        )

    def test_06_no_emojis_in_ui_flet(self):
        """src/ui_flet modülündeki tüm dosyalarda hiçbir emoji olmamalıdır."""
        flet_dir = BASE_DIR / "src" / "ui_flet"
        for py_file in flet_dir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            emojis_found = EMOJI_PATTERN.findall(content)
            self.assertEqual(
                len(emojis_found),
                0,
                f"{py_file.name} içinde istenmeyen emojiler tespit edildi: {set(emojis_found)}",
            )


if __name__ == "__main__":
    unittest.main()


