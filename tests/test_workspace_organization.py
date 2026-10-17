"""Çalışma alanı ve klasör düzeni doğrulama birim testleri."""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff]"
    r"|[\u2600-\u27bf]"
    r"|[\u2300-\u23ff]"
)


class TestWorkspaceOrganization(unittest.TestCase):
    """Proje klasör yapısı, dokümantasyon konumu ve sıfır emoji kurallarını denetler."""

    def test_01_docs_directory_exists_and_contains_plan_and_product(self):
        """Dokümantasyon dosyaları docs/ klasöründe bulunmalıdır."""
        docs_dir = BASE_DIR / "docs"
        self.assertTrue(docs_dir.is_dir(), "docs/ klasörü mevcut olmalıdır.")

        plan_file = docs_dir / "turkish_stt_diarization_plan.md"
        self.assertTrue(plan_file.is_file(), "turkish_stt_diarization_plan.md docs/ altında bulunmalıdır.")

        product_file = docs_dir / "PRODUCT.md"
        self.assertTrue(product_file.is_file(), "PRODUCT.md docs/ altında bulunmalıdır.")

        # Kök dizinde dağınıklık olmamalı
        root_plan = BASE_DIR / "turkish_stt_diarization_plan.md"
        self.assertFalse(root_plan.exists(), "Kök dizinde turkish_stt_diarization_plan.md bulunmamalıdır.")
        root_product = BASE_DIR / "PRODUCT.md"
        self.assertFalse(root_product.exists(), "Kök dizinde mükerrer PRODUCT.md bulunmamalıdır.")
        root_setup_env = BASE_DIR / "setup_env.bat"
        self.assertFalse(root_setup_env.exists(), "Kök dizinde gereksiz setup_env.bat bulunmamalıdır.")

        # src/updater.py modülünün varlığı
        updater_file = BASE_DIR / "src" / "updater.py"
        self.assertTrue(updater_file.is_file(), "src/updater.py mevcut olmalıdır.")

    def test_02_directories_and_gitkeep_exist(self):
        """Gerekli çalışma dizinleri ve gitkeep dosyaları mevcut olmalıdır."""
        for dname in ["src", "tests", "docs", "outputs", "temp", "models"]:
            dpath = BASE_DIR / dname
            self.assertTrue(dpath.is_dir(), f"{dname} klasörü mevcut olmalıdır.")

        self.assertTrue((BASE_DIR / "outputs" / ".gitkeep").is_file(), "outputs/.gitkeep mevcut olmalıdır.")
        self.assertTrue((BASE_DIR / "temp").is_dir(), "temp klasörü mevcut olmalıdır.")

    def test_03_gitignore_contains_necessary_rules(self):
        """.gitignore dosyası kritik geçici ve özel dizinleri içermelidir."""
        gitignore_file = BASE_DIR / ".gitignore"
        self.assertTrue(gitignore_file.is_file(), ".gitignore mevcut olmalıdır.")

        with open(gitignore_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("temp/", content)
        self.assertIn("outputs/", content)
        self.assertIn("models/", content)
        self.assertIn(".impeccable", content)

    def test_04_no_emojis_in_docs(self):
        """docs/ klasöründeki belgelerde hiçbir emoji olmamalıdır."""
        docs_dir = BASE_DIR / "docs"
        if docs_dir.exists():
            for doc in docs_dir.glob("*.md"):
                with open(doc, "r", encoding="utf-8") as f:
                    text = f.read()
                emojis = EMOJI_PATTERN.findall(text)
                self.assertEqual(len(emojis), 0, f"{doc.name} içinde emoji bulundu: {set(emojis)}")

    def test_05_main_py_check_mode(self):
        """main.py --check parametresi ile başlatıldığında GUI açmadan sıfır çıkış koduyla doğrulamalıdır."""
        python_exe = sys.executable
        res = subprocess.run(
            [python_exe, "main.py", "--check"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(res.returncode, 0, f"main.py --check başarısız: {res.stderr}")
        self.assertIn("DOĞRULAMA BAŞARILI", res.stdout)


if __name__ == "__main__":
    unittest.main()
