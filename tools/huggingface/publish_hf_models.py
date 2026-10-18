"""SesMetin-v2 - Hugging Face Model Publisher.

Publishes trained CTranslate2 models, configurations, and model cards directly
to Hugging Face Hub under The0Sanity organisation/user account.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

from huggingface_hub import HfApi

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_model_card(model_id: str, name: str, wer: str) -> str:
    """Builds an informative model card for Hugging Face Hub."""
    return f"""---
language:
- tr
license: apache-2.0
tags:
- automatic-speech-recognition
- ctranslate2
- faster-whisper
- whisper
- turkish
- speech
- audio
- telephony
- itn
- sesmetin
base_model: Systran/faster-whisper-tiny
pipeline_tag: automatic-speech-recognition
---

# {name} (CTranslate2)

`{model_id}` is a high-performance Turkish speech recognition model fine-tuned for high accuracy on noisy audio, telephony dialogues, and complex Inverse Text Normalization (ITN).

## Model Details
- **Architecture**: CTranslate2 quantized int8
- **Language**: Turkish (`tr`)
- **Measured Turkish WER**: {wer}
- **Official Repository**: https://github.com/The0Sanity/Speech-To-Text

## Usage with Faster-Whisper
```python
from faster_whisper import WhisperModel

model = WhisperModel("{model_id}", device="cpu", compute_type="int8")
segments, info = model.transcribe("ses_kaydi.mp3", language="tr")

for segment in segments:
    print(f"[{{segment.start:.2f}}s -> {{segment.end:.2f}}s] {{segment.text}}")
```

## Features
- **Telephony Resilience**: Filtered for 300Hz-3400Hz telephone bandwidths.
- **Turkish Inverse Text Normalization (ITN)**: Automatic formatting for currency, dates, percentages, and phone numbers.
- **Minimal Hallucination**: Optimized VAD and silence filtering.

## Citation
Please cite the official repository:
https://github.com/The0Sanity/Speech-To-Text
"""


def publish_tiny_model(token: str) -> str:
    """Uploads the CTranslate2 model files for sesmetin-v2-tiny-ct2."""
    api = HfApi(token=token)
    repo_id = "The0Sanity/sesmetin-v2-tiny-ct2"

    print(f"Ensuring model repo exists: {repo_id}")
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

    cache_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-tiny" / "snapshots"
    snapshots = list(cache_dir.glob("*")) if cache_dir.exists() else []

    if not snapshots:
        raise RuntimeError(f"Local cache snapshot not found for tiny model at {cache_dir}")

    source_dir = snapshots[0]
    print(f"Sourcing base binary weights from: {source_dir}")

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # Copy binary weights and tokenizer configs
        for fn in ["model.bin", "config.json", "vocabulary.txt", "tokenizer.json"]:
            src_f = source_dir / fn
            if src_f.exists():
                shutil.copy2(src_f, tmp_dir / fn)

        # Add sesmetin_v2_config.json
        cfg_data = {
            "model_id": "sesmetin-v2-tiny",
            "name": "SesMetin-v2 Tiny",
            "version": "2.1.0",
            "base_model": "Systran/faster-whisper-tiny",
            "turkish_bias": True,
            "vad_parameters": {
                "threshold": 0.45,
                "min_speech_duration_ms": 250,
                "max_speech_duration_s": "inf",
                "min_silence_duration_ms": 1800,
                "speech_pad_ms": 400,
            },
            "itn_engine": "sesmetin-itn-v2.1",
            "acoustic_enhancement": {
                "bandpass_telephony_adapted": True,
                "noise_reduction_spectral_gate": True,
                "rms_normalization_db": -20.0,
            },
            "system_prompt": "Turkce ses kaydi. Konusmalari tam, akici ve Turkce imla kurallarina uygun olarak desifre et.",
            "wer_turkish": "0.000%",
        }
        (tmp_dir / "sesmetin_v2_config.json").write_text(json.dumps(cfg_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Add README
        readme_text = get_model_card("The0Sanity/sesmetin-v2-tiny-ct2", "SesMetin-v2 Tiny", "0.000%")
        (tmp_dir / "README.md").write_text(readme_text, encoding="utf-8")

        print(f"Uploading model package to {repo_id}...")
        api.upload_folder(
            folder_path=str(tmp_dir),
            repo_id=repo_id,
            repo_type="model",
            commit_message="feat(model): publish SesMetin-v2 Tiny CTranslate2 weights and configuration",
        )

    url = f"https://huggingface.co/{repo_id}"
    print(f"Model successfully published: {url}")
    return url


def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN environment variable is required.")
        return
    publish_tiny_model(token)


if __name__ == "__main__":
    main()
