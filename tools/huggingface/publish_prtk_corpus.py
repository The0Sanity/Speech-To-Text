"""Publish Prtk YouTube speech & transcript corpus to Hugging Face Hub.

Official Repository: https://github.com/The0Sanity/Speech-To-Text
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi, create_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PublishPrtkCorpus")

DEFAULT_REPO_ID = "The0Sanity/sesmetin-v2-prtk-speech-corpus"
DEFAULT_DATA_DIR = Path("dataset/prtk_speech_corpus")


def generate_dataset_card(summary: dict) -> str:
    """Generates a comprehensive dataset card in Markdown format without any emojis."""
    return f"""---
language:
- tr
task_categories:
- automatic-speech-recognition
license: apache-2.0
size_categories:
- 1K<n<10K
tags:
- speech-recognition
- whisper
- turkish
- sesmetin
- conversational
- educational
---

# SesMetin-v2 Prtk YouTube Speech Corpus

Official Repository: https://github.com/The0Sanity/Speech-To-Text

## Overview
This dataset contains paired Turkish speech transcript segments extracted directly from the official Prtk YouTube channel (`https://www.youtube.com/@Prtk/videos`).
Transcriptions were harvested using the official YouTube transcript renderer components (`ytd-video-description-transcript-section-renderer` and `ytd-engagement-panel-section-list-renderer` / `PAmodern_transcript_view`) and synchronized timedtext caption streams.

## Dataset Statistics
- Source Channel: `{summary.get("channel_url", "https://www.youtube.com/@Prtk/videos")}`
- Videos Sampled: {summary.get("transcripts_extracted", 0)}
- Total Speech Segments: {summary.get("total_segments", 0)}
- Training Records: {summary.get("train_samples", 0)}
- Validation Records: {summary.get("validation_samples", 0)}
- Test Records: {summary.get("test_samples", 0)}

## Data Structure
Each segment record in `prtk_segments.parquet` contains:
- `video_id`: 11-character YouTube video identifier
- `title`: Sanitized video title (emojis removed)
- `url`: Direct canonical URL to the YouTube video
- `start`: Segment start timestamp in seconds
- `end`: Segment end timestamp in seconds
- `duration`: Segment duration in seconds
- `text`: Clean Turkish transcription text

## Cleanliness & Normalization
1. All non-standard Unicode emojis and presentation symbols have been stripped.
2. Bracketed non-speech sound markers (e.g. `[muzik]`, `(alkis)`) have been removed.
3. Whitespace and punctuation normalized for ASR acoustic model fine-tuning.

## License & Attribution
Distributed under Apache-2.0 License.
Attribution: https://github.com/The0Sanity/Speech-To-Text
"""


def publish_corpus(
    repo_id: str = DEFAULT_REPO_ID,
    data_dir: Path = DEFAULT_DATA_DIR,
    token: Optional[str] = None
) -> str:
    """Uploads the Prtk corpus files to Hugging Face Hub."""
    token = token or os.environ.get("HF_TOKEN")
    api = HfApi(token=token)

    logger.info("Ensuring Hugging Face dataset repository exists: %s", repo_id)
    create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True, token=token)

    summary_file = data_dir / "dataset_summary.json"
    summary = {}
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

    # Write README.md
    readme_path = data_dir / "README.md"
    readme_content = generate_dataset_card(summary)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    logger.info("Uploading corpus files from %s to %s...", data_dir, repo_id)
    files_to_upload = [
        "README.md",
        "dataset_summary.json",
        "train.json",
        "validation.json",
        "test.json",
    ]
    parquet_path = data_dir / "prtk_segments.parquet"
    if parquet_path.exists():
        files_to_upload.append("prtk_segments.parquet")

    for fname in files_to_upload:
        fpath = data_dir / fname
        if fpath.exists():
            logger.info("Uploading %s...", fname)
            api.upload_file(
                path_or_fileobj=str(fpath),
                path_in_repo=fname,
                repo_id=repo_id,
                repo_type="dataset",
                token=token,
                commit_message=f"Upload Prtk corpus {fname}",
            )

    hub_url = f"https://huggingface.co/datasets/{repo_id}"
    logger.info("Successfully published Prtk speech corpus to %s", hub_url)
    return hub_url


if __name__ == "__main__":
    url = publish_corpus()
    print("Hub Dataset URL:", url)
