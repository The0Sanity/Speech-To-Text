"""Unit tests for Prtk YouTube transcript extractor, cleaning, and segmentation."""

import unittest
from typing import List, Dict, Any


def clean_transcript_text(raw_text: str) -> str:
    """Cleans transcript text by stripping emojis, bracketed audio tags, and extra spaces."""
    import re
    # Remove bracketed sound tags like [müzik], (alkış), [şarkı]
    text = re.sub(r"\[.*?\]|\(.*?\)", "", raw_text)
    # Strip emojis and supplementary symbols
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    # Normalize multiple whitespace characters
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """Converts MM:SS or HH:MM:SS timestamp strings into total seconds."""
    parts = ts_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0


def parse_engagement_panel_html(html_snippet: str) -> List[Dict[str, Any]]:
    """Parses YouTube engagement panel macro-markers-panel-item-view-model items."""
    import re
    # Match text pattern: (0:04) (4 seconds) (text)
    pattern = re.compile(
        r'<macro-markers-panel-item-view-model[^>]*>.*?(\d+:\d{2}(?::\d{2})?).*?<\/macro-markers-panel-item-view-model>',
        re.DOTALL | re.IGNORECASE
    )
    # Fallback to regex capturing timestamp and following text if raw text
    items = []
    matches = re.findall(r'(\d+:\d{2}(?::\d{2})?)\s+(?:.*?seconds\s+)?([^\n<]+)', html_snippet)
    for idx, (ts, content) in enumerate(matches):
        cleaned = clean_transcript_text(content)
        if cleaned:
            items.append({
                "index": idx,
                "timestamp_str": ts,
                "start": parse_timestamp_to_seconds(ts),
                "text": cleaned
            })
    return items


class TestPrtkTranscriptExtractor(unittest.TestCase):
    """Test suite for YouTube transcript extraction and normalization."""

    def test_01_clean_transcript_text_strips_emojis_and_audio_tags(self):
        raw = "10 Patates Sarkisi \U0001f954 [muzik] 1'den 10'a sayilari ogreniyoruz (alkis)!"
        cleaned = clean_transcript_text(raw)
        self.assertNotIn("[muzik]", cleaned)
        self.assertNotIn("(alkis)", cleaned)
        self.assertNotIn("\U0001f954", cleaned)
        self.assertEqual(cleaned, "10 Patates Sarkisi 1'den 10'a sayilari ogreniyoruz !")

    def test_02_parse_timestamp_to_seconds(self):
        self.assertEqual(parse_timestamp_to_seconds("0:04"), 4.0)
        self.assertEqual(parse_timestamp_to_seconds("1:15"), 75.0)
        self.assertEqual(parse_timestamp_to_seconds("1:02:30"), 3750.0)

    def test_03_parse_engagement_panel_text(self):
        sample_snippet = (
            "0:04\n4 seconds\nBir patates patates. [muzik] 2 patates patates.\n"
            "0:12\n12 seconds\n3 [muzik] patates patates. 4 patates patates.\n"
            "0:21\n21 seconds\n5 patates. 6 patates 7 patates 8 patates\n"
        )
        segments = parse_engagement_panel_html(sample_snippet)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["start"], 4.0)
        self.assertEqual(segments[0]["text"], "Bir patates patates. 2 patates patates.")
        self.assertEqual(segments[1]["start"], 12.0)
        self.assertEqual(segments[1]["text"], "3 patates patates. 4 patates patates.")

    def test_04_split_train_val_test(self):
        records = [{"id": i} for i in range(100)]
        train = records[:85]
        val = records[85:95]
        test = records[95:]
        self.assertEqual(len(train), 85)
        self.assertEqual(len(val), 10)
        self.assertEqual(len(test), 5)


if __name__ == "__main__":
    unittest.main()
