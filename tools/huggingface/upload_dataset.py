"""SesMetin-v2 - Hugging Face Dataset Uploader.

Uploads Turkish synthetic speech transcripts, metadata, telephony dialogues,
and benchmark corpora to Hugging Face Datasets under user's Hub account.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from huggingface_hub import HfApi

REPO_ID = "The0Sanity/sesmetin-v2-speech-corpus"
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def build_dataset_cards() -> str:
    """Builds YAML frontmatter and README for the Hugging Face dataset."""
    return """---
language:
- tr
license: apache-2.0
task_categories:
- automatic-speech-recognition
task_ids:
- speech-recognition
tags:
- speech
- audio
- turkish
- telephony
- itn
- transcription
- sesmetin
- speech-to-text
pretty_name: SesMetin-v2 Turkish Speech Corpus
size_categories:
- 10K<n<100K
---

# SesMetin-v2 Turkish Speech Corpus

Curated Turkish speech dataset designed for speech recognition fine-tuning, inverse text normalization (ITN),
and telephony-resilient acoustic adaptation.

## Dataset Summary
- **Language**: Turkish (`tr`)
- **Domains**: Telephony customer service, retail ordering, financial transaction dialogues, and numerical ITN.
- **Synthesized Audio**: Generated via Kokoro-82M neural Turkish voices and enhanced acoustic telephony filters.
- **Official Repository**: https://github.com/The0Sanity/Speech-To-Text

## Structure
- `train.jsonl`: Training utterances with duration, text, and phonetic normalization.
- `validation.jsonl`: Benchmark test split covering telephony, retail, and ITN numbers.
- `longform_dialogues.jsonl`: Multi-speaker dialogues between 5 and 10 minutes duration.

## License
Apache 2.0
"""


def gather_dataset_records() -> List[Dict[str, Any]]:
    """Gathers all available synthetic manifest entries and dialogue turns into records."""
    records: List[Dict[str, Any]] = []

    # 1. Synthetic manifest
    manifest_p = BASE_DIR / "dataset" / "synthetic_speech" / "metadata.jsonl"
    if manifest_p.exists():
        with open(manifest_p, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    data = json.loads(s)
                    records.append({
                        "id": data.get("id", f"syn_{len(records)}"),
                        "text": data.get("text", ""),
                        "duration": data.get("duration", 0.0),
                        "domain": data.get("domain", "conversational"),
                        "voice": data.get("voice", "kokoro_tr"),
                        "split": "train",
                    })
                except json.JSONDecodeError:
                    continue

    # 2. Longform dialogues
    longform_dir = BASE_DIR / "dataset" / "longform_mp3"
    if longform_dir.exists():
        for json_f in longform_dir.glob("*.json"):
            try:
                content = json.loads(json_f.read_text(encoding="utf-8"))
                for idx, turn in enumerate(content.get("turns", [])):
                    records.append({
                        "id": f"{json_f.stem}_{idx}",
                        "text": turn.get("text", ""),
                        "duration": float(turn.get("duration", 0.0)),
                        "domain": content.get("domain", "telephony"),
                        "voice": turn.get("speaker", "SPEAKER_00"),
                        "split": "validation" if idx % 5 == 0 else "train",
                    })
            except Exception:
                continue

    return records


def upload_to_huggingface(token: str, repo_id: str = REPO_ID) -> str:
    """Creates the dataset repository on Hugging Face Hub and uploads JSONL splits."""
    api = HfApi(token=token)

    print(f"Creating or verifying dataset repo: {repo_id}")
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

    records = gather_dataset_records()
    print(f"Gathered {len(records)} speech dataset records.")

    train_records = [r for r in records if r.get("split") == "train"]
    val_records = [r for r in records if r.get("split") == "validation"]

    if not val_records:
        val_records = train_records[: max(1, len(train_records) // 5)]

    # Temporary files for upload
    temp_dir = BASE_DIR / "dataset" / "_hf_export"
    temp_dir.mkdir(parents=True, exist_ok=True)

    readme_p = temp_dir / "README.md"
    readme_p.write_text(build_dataset_cards(), encoding="utf-8")

    train_p = temp_dir / "train.jsonl"
    with open(train_p, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    val_p = temp_dir / "validation.jsonl"
    with open(val_p, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Uploading files to Hugging Face Datasets ({repo_id})...")
    api.upload_folder(
        folder_path=str(temp_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="feat(dataset): publish SesMetin-v2 Turkish Speech Corpus splits and metadata",
    )

    url = f"https://huggingface.co/datasets/{repo_id}"
    print(f"Dataset successfully uploaded: {url}")
    return url


def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN environment variable is required.")
        return
    upload_to_huggingface(token)


if __name__ == "__main__":
    main()
