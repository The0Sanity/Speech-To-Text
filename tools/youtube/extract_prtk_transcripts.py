"""Prtk YouTube Channel Transcript & Audio Alignment Pipeline.

Official Repository: https://github.com/The0Sanity/Speech-To-Text

Extracts transcripts from YouTube videos using official transcript structures
(ytd-video-description-transcript-section-renderer and ytd-engagement-panel-section-list-renderer
via player captionTracks and timedtext endpoints).
Normalizes text, strips emojis and sound annotations, and partitions into train/val/test splits.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Enforce UTF-8 on Windows stdout/stderr to eliminate cp1254 UnicodeEncodeErrors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PrtkTranscriptExtractor")

CHANNEL_URL = "https://www.youtube.com/@Prtk/videos"
OUTPUT_DIR = Path("dataset/prtk_speech_corpus")


def clean_transcript_text(raw_text: str) -> str:
    """Cleans transcript text by stripping emojis, bracketed audio tags, and extra spaces."""
    if not raw_text:
        return ""
    # Strip HTML entities
    text = raw_text.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
    # Remove bracketed sound tags like [müzik], (alkış), [şarkı]
    text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    # Strip emojis and supplementary Unicode symbols
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    text = re.sub(r"[\u2600-\u27bf]", "", text)
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


def _get_extractor_args() -> Dict[str, Any]:
    """Extractor arguments for bypassing bot detection and accessing player tracks."""
    return {
        "youtube": {
            "player_client": ["android", "ios", "mweb"],
        }
    }


def fetch_channel_videos(channel_url: str = CHANNEL_URL) -> List[Dict[str, Any]]:
    """Retrieves all video metadata from the YouTube channel."""
    logger.info("Querying video catalog from: %s", channel_url)
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "no_warnings": True,
        "extractor_args": _get_extractor_args(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        raw_entries = info.get("entries", [])
        videos = []
        for e in raw_entries:
            vid = e.get("id")
            title = e.get("title") or ""
            title_clean = clean_transcript_text(title)
            duration = e.get("duration") or 0.0
            if vid:
                videos.append({
                    "id": vid,
                    "title": title_clean,
                    "duration": duration,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                })
        logger.info("Discovered %d videos from channel.", len(videos))
        return videos


def fetch_video_transcript_segments(video_id: str) -> List[Dict[str, Any]]:
    """Fetches and parses official Turkish transcript segments for a given video."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["tr", "tr-orig"],
        "extractor_args": _get_extractor_args(),
    }

    segments: List[Dict[str, Any]] = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            subs = info.get("subtitles", {}) or {}
            auto_subs = info.get("automatic_captions", {}) or {}

            sub_tracks = (
                subs.get("tr")
                or subs.get("tr-orig")
                or auto_subs.get("tr")
                or auto_subs.get("tr-orig")
                or []
            )
            if not sub_tracks:
                return []

            target_track = None
            for track in sub_tracks:
                if track.get("ext") == "json3":
                    target_track = track
                    break
            if not target_track and sub_tracks:
                target_track = sub_tracks[0]

            track_url = target_track.get("url")
            if not track_url:
                return []

            req = urllib.request.Request(track_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            if target_track.get("ext") == "json3" or content.strip().startswith("{"):
                data = json.loads(content)
                events = data.get("events", [])
                for ev in events:
                    start_ms = ev.get("tStartMs", 0)
                    dur_ms = ev.get("dDurationMs", 0)
                    segs = ev.get("segs", [])
                    raw_text = "".join([s.get("utf8", "") for s in segs]).strip()
                    cleaned_text = clean_transcript_text(raw_text)
                    if cleaned_text and cleaned_text != "\n":
                        segments.append({
                            "start": round(start_ms / 1000.0, 3),
                            "end": round((start_ms + dur_ms) / 1000.0, 3),
                            "text": cleaned_text,
                        })
            else:
                try:
                    root = ET.fromstring(content)
                    for elem in root.findall(".//text"):
                        start_sec = float(elem.attrib.get("start", 0.0))
                        dur_sec = float(elem.attrib.get("dur", 0.0))
                        cleaned_text = clean_transcript_text(elem.text or "")
                        if cleaned_text:
                            segments.append({
                                "start": round(start_sec, 3),
                                "end": round(start_sec + dur_sec, 3),
                                "text": cleaned_text,
                            })
                except Exception as xml_err:
                    logger.debug("XML parse fallback error: %s", xml_err)

    except Exception as e:
        logger.debug("Transcript retrieval failed for %s: %s", video_id, e)

    return segments


def build_prtk_corpus(
    max_videos: Optional[int] = None,
    output_dir: Path = OUTPUT_DIR
) -> Dict[str, Any]:
    """Extracts transcripts for channel videos and constructs dataset splits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    videos = fetch_channel_videos()
    if max_videos:
        videos = videos[:max_videos]

    all_records: List[Dict[str, Any]] = []

    logger.info("Extracting transcripts for %d videos...", len(videos))
    for idx, v in enumerate(videos):
        vid = v["id"]
        title = v["title"]
        dur = v["duration"]
        segments = fetch_video_transcript_segments(vid)
        if segments:
            full_text = " ".join(s["text"] for s in segments)
            record = {
                "video_id": vid,
                "title": title,
                "duration": dur,
                "url": v["url"],
                "total_segments": len(segments),
                "segments": segments,
                "full_transcript": full_text,
            }
            all_records.append(record)

        if (idx + 1) % 10 == 0 or idx == len(videos) - 1:
            logger.info(
                "Processed %d/%d videos - Collected %d transcripts (%d total segments)",
                idx + 1,
                len(videos),
                len(all_records),
                sum(r["total_segments"] for r in all_records),
            )
        time.sleep(0.05)

    n_total = len(all_records)
    n_train = max(1, int(n_total * 0.85)) if n_total > 1 else n_total
    n_val = max(1, int(n_total * 0.10)) if n_total > 2 else 0

    train_records = all_records[:n_train]
    val_records = all_records[n_train:n_train + n_val]
    test_records = all_records[n_train + n_val:]

    dataset_summary = {
        "channel_url": CHANNEL_URL,
        "total_videos_checked": len(videos),
        "transcripts_extracted": n_total,
        "train_samples": len(train_records),
        "validation_samples": len(val_records),
        "test_samples": len(test_records),
        "total_segments": sum(r["total_segments"] for r in all_records),
    }

    with open(output_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_records, f, ensure_ascii=False, indent=2)
    with open(output_dir / "validation.json", "w", encoding="utf-8") as f:
        json.dump(val_records, f, ensure_ascii=False, indent=2)
    with open(output_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_records, f, ensure_ascii=False, indent=2)
    with open(output_dir / "dataset_summary.json", "w", encoding="utf-8") as f:
        json.dump(dataset_summary, f, ensure_ascii=False, indent=2)

    # Also export flat parquet for Hugging Face datasets streaming
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        flat_segments = []
        for r in all_records:
            for seg in r["segments"]:
                flat_segments.append({
                    "video_id": r["video_id"],
                    "title": r["title"],
                    "url": r["url"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "duration": round(seg["end"] - seg["start"], 3),
                    "text": seg["text"],
                })

        if flat_segments:
            table = pa.Table.from_pylist(flat_segments)
            pq.write_table(table, output_dir / "prtk_segments.parquet", compression="snappy")
            logger.info("Exported %d flat segments to Parquet format.", len(flat_segments))
    except ImportError:
        logger.debug("pyarrow not available; skipping parquet serialization.")

    logger.info(
        "Corpus construction complete: %d train, %d val, %d test videos (%d total segments)",
        len(train_records),
        len(val_records),
        len(test_records),
        dataset_summary["total_segments"],
    )
    return dataset_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract transcripts from Prtk YouTube channel.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of videos to process.")
    parser.add_argument("--output-dir", type=str, default="dataset/prtk_speech_corpus", help="Output directory.")
    args = parser.parse_args()

    summary = build_prtk_corpus(max_videos=args.limit, output_dir=Path(args.output_dir))
    print(json.dumps(summary, indent=2))
