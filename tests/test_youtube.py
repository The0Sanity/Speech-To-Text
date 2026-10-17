"""YouTube modülü testleri."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.youtube_downloader import (
    extract_video_id,
    is_valid_youtube_url,
)


class TestYouTubeDownloader(unittest.TestCase):
    """YouTube URL doğrulama ve analiz testleri."""

    def test_valid_urls(self):
        """Geçerli YouTube adreslerinin doğrulanması."""
        valid_samples = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
        ]
        for url in valid_samples:
            self.assertTrue(is_valid_youtube_url(url), f"Başarısız URL: {url}")
            self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ", f"Yanlış ID: {url}")

    def test_invalid_urls(self):
        """Geçersiz adreslerin reddedilmesi."""
        invalid_samples = [
            "",
            "   ",
            "https://google.com",
            "https://vimeo.com/123456",
            "https://youtube.com/not_a_video",
            "not a url",
        ]
        for url in invalid_samples:
            self.assertFalse(is_valid_youtube_url(url), f"Geçersiz olması gereken URL onaylandı: {url}")
    def test_fetch_video_info_user_url(self):
        """Kullanıcının belirttiği PHMGFHNLMG4 videosunun bot korumasına takılmadan çekilmesi."""
        from src.youtube_downloader import get_youtube_video_info

        url = "https://www.youtube.com/watch?v=PHMGFHNLMG4"
        info = get_youtube_video_info(url)
        self.assertIn("VALORANT", info["title"].upper())
        self.assertEqual(info["duration_formatted"], "03:42")
        self.assertEqual(info["channel"], "Saniye")


if __name__ == "__main__":
    unittest.main()
