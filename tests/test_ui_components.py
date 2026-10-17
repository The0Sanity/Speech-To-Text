"""Modern UI bileşenleri, stil sistemi ve yardımcı fonksiyon testleri."""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.exporter import (
    export_to_markdown,
    export_to_vtt,
    to_vtt_timestamp,
)
from src.ui.style import (
    THEMES,
    get_speaker_color,
    get_theme_palette,
)


class TestUIComponentsAndStyling(unittest.TestCase):
    """UI stil, tema, istatistik ve dışa aktarma testleri."""

    def setUp(self):
        self.sample_transcript = [
            {
                "id": 1,
                "start": 0.0,
                "end": 2.5,
                "speaker": "X1",
                "text": "Merhaba, bugünkü toplantıya hoş geldiniz.",
                "timestamp_display": "[00:00 - 00:02]",
            },
            {
                "id": 2,
                "start": 2.8,
                "end": 5.4,
                "speaker": "X2",
                "text": "Teşekkür ederim, projeyi değerlendireceğiz.",
                "timestamp_display": "[00:02 - 00:05]",
            },
            {
                "id": 3,
                "start": 5.8,
                "end": 9.0,
                "speaker": "X1",
                "text": "İlk gündem maddemiz yapay zeka modelidir.",
                "timestamp_display": "[00:05 - 00:09]",
            },
        ]
        self.media_info = {
            "file_name": "toplanti_kaydi.mp4",
            "duration_formatted": "00:09",
            "duration_seconds": 9.0,
            "file_size_mb": 4.2,
        }

    def test_01_theme_palettes(self):
        """Karanlık ve Aydınlık tema paletlerinin tüm tokenleri içermesi testi."""
        self.assertIn("dark", THEMES)
        self.assertIn("light", THEMES)

        required_tokens = [
            "bg_app",
            "bg_card",
            "bg_card_secondary",
            "border_card",
            "accent_primary",
            "accent_hover",
            "text_main",
            "text_muted",
            "text_subtle",
            "success",
            "warning",
            "danger",
        ]

        dark = get_theme_palette("dark")
        light = get_theme_palette("light")

        for token in required_tokens:
            self.assertIn(token, dark, f"Dark theme missing token: {token}")
            self.assertIn(token, light, f"Light theme missing token: {token}")
            self.assertTrue(dark[token].startswith("#"), f"Token {token} must be hex")
            self.assertTrue(light[token].startswith("#"), f"Token {token} must be hex")

    def test_02_speaker_colors(self):
        """Konuşmacı renklerinin deterministik ve geçerli hex kodları üretmesi."""
        # Standart etiket
        bg1, fg1 = get_speaker_color("X1")
        self.assertTrue(bg1.startswith("#"))
        self.assertTrue(fg1.startswith("#"))

        # Özel isimli etiket
        bg_ahmet, fg_ahmet = get_speaker_color("Ahmet Bey")
        self.assertTrue(bg_ahmet.startswith("#"))
        self.assertEqual(fg_ahmet, "#ffffff")

        # Determinizm (Aynı isim her zaman aynı rengi vermeli)
        bg_ahmet_2, _ = get_speaker_color("Ahmet Bey")
        self.assertEqual(bg_ahmet, bg_ahmet_2)

    def test_03_vtt_export(self):
        """WebVTT altyazı formatı dönüşümü testi."""
        # Zaman damgası formatı: 00:00:02.500
        vtt_ts = to_vtt_timestamp(2.5)
        self.assertEqual(vtt_ts, "00:00:02.500")

        temp_vtt = BASE_DIR / "temp" / "test_out.vtt"
        try:
            export_to_vtt(self.sample_transcript, str(temp_vtt), include_speaker=True)
            self.assertTrue(temp_vtt.exists())
            with open(temp_vtt, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertTrue(content.startswith("WEBVTT"))
            self.assertIn("<v X1>", content)
            self.assertIn("-->", content)
            self.assertIn("Merhaba, bugünkü toplantıya hoş geldiniz.", content)
        finally:
            if temp_vtt.exists():
                os.remove(temp_vtt)

    def test_04_markdown_export(self):
        """Markdown dökümanı formatı dışa aktarma testi."""
        temp_md = BASE_DIR / "temp" / "test_out.md"
        try:
            export_to_markdown(self.sample_transcript, str(temp_md), self.media_info)
            self.assertTrue(temp_md.exists())
            with open(temp_md, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# 🎙️ Ses Transkript Raporu", content)
            self.assertIn("toplanti_kaydi.mp4", content)
            self.assertIn("**X1**", content)
            self.assertIn("**X2**", content)
        finally:
            if temp_md.exists():
                os.remove(temp_md)

    def test_05_transcript_analytics_and_stats(self):
        """Transkript istatistik hesaplama doğrulaması."""
        from src.aligner import compute_transcript_statistics

        stats = compute_transcript_statistics(self.sample_transcript)
        self.assertEqual(stats["total_turns"], 3)
        self.assertEqual(stats["unique_speakers_count"], 2)
        self.assertIn("X1", stats["speaker_speaking_times"])
        self.assertIn("X2", stats["speaker_speaking_times"])
        self.assertGreater(stats["total_words"], 10)
        self.assertGreater(stats["speaking_duration_seconds"], 5.0)

    def test_06_find_and_replace_in_transcript(self):
        """Transkript içinde kelime bulma ve değiştirme."""
        from src.aligner import find_and_replace_in_transcript

        updated, count = find_and_replace_in_transcript(
            self.sample_transcript,
            find_str="toplantıya",
            replace_str="seminere",
            case_sensitive=False,
        )
        self.assertEqual(count, 1)
        self.assertIn("seminere", updated[0]["text"])

    def test_07_filter_transcript(self):
        """Transkript arama ve filtreleme testi."""
        from src.aligner import filter_transcript

        # Metin araması
        res1 = filter_transcript(self.sample_transcript, "proje")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["speaker"], "X2")

        # Konuşmacı araması
        res2 = filter_transcript(self.sample_transcript, "X1")
        self.assertEqual(len(res2), 2)

        # Olmayan kelime
        res3 = filter_transcript(self.sample_transcript, "astronomi")
        self.assertEqual(len(res3), 0)


if __name__ == "__main__":
    unittest.main()
