<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Offline Turkish speech-to-text with speaker labels, for Windows

[![Release](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=Release)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/The0Sanity/Speech-To-Text/release.yml?branch=main&label=Build)](https://github.com/The0Sanity/Speech-To-Text/actions)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![License](https://img.shields.io/badge/License-MIT%20%2B%20Visual%20Attribution-F59E0B)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## What it does

SesMetin Pro turns audio and video files, or a YouTube link, into a
timestamped Turkish transcript with speaker labels (X1, X2, ...), which you
can correct and export. Recognition runs on your own computer with OpenAI
Whisper models through faster-whisper; your audio and transcripts are not
uploaded anywhere.

The network is used for three things only: downloading a model the first time
you pick it, fetching audio when you give a YouTube link, and checking GitHub
for a new version.

## Features

- **Transcription:** Whisper Tiny, Base, Small, Medium, Large-v3 and
  Large-v3-Turbo, on CPU (INT8) or an NVIDIA GPU. Models are downloaded and
  deleted from inside the app.
- **Speaker labels:** segments are grouped by voice and labelled X1, X2, ...;
  you can rename speakers. This is a simple acoustic clustering and its
  accuracy has not been measured.
- **Turkish number formatting:** spoken numbers, percentages, currencies and
  ordinals are written as digits ("yüzde yirmi beş" becomes "%25").
- **Input:** MP4, MP3, WAV, M4A, AAC, MKV, FLAC, OGG, or a YouTube link
  (through `yt-dlp`). FFmpeg is downloaded on first run if it is missing.
- **Editing:** search, find and replace, speaker rename.
- **Export:** `.txt`, `.srt`, `.vtt`, `.json`, `.csv`, `.md`, or copy to the
  clipboard.
- **Updates:** the app checks GitHub Releases and updates itself after one
  click.

## Measured accuracy

Word error rate on 150 clips of the FLEURS Turkish test set, measured through
the app's own pipeline. Lower is better.

| Model | v1.1.5 | v1.1.7 |
| :--- | :--- | :--- |
| Whisper Tiny | 67.38% | 41.07% |
| Whisper Small | 32.62% | 15.18% |

The other models have not been measured. FLEURS is short read sentences from
one speaker; interviews, phone audio and music will behave differently. The
method, every run and the limits are in [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

## Install

1. Open [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases).
2. Download `SpeechToText-Setup.exe` (installer) or `SpeechToText.exe`
   (portable, no installation).
3. Run it.

> [!NOTE]
> **Windows SmartScreen:** the release files are not signed with a
> certificate Windows trusts, so the first launch shows *"Windows protected
> your PC"*. Click **"More info"**, then **"Run anyway"**. Each release
> lists the SHA-256 of both files so you can check your download.

> [!IMPORTANT]
> **Updating from any earlier release:** the built-in updater in those
> versions does not work reliably. Download v1.1.7 or newer by hand once;
> after that, in-app updates work. This includes the release published as
> v1.1.6, which was built from v1.1.5 source and reports itself as 1.1.5.

### Running from source

```powershell
git clone https://github.com/The0Sanity/Speech-To-Text.git
cd Speech-To-Text
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Tests: `python -m pytest tests`.

## About the "SesMetin" models

Versions up to v1.1.5 offered six "SesMetin" models. The three v2 model files
are byte-identical to the stock Whisper models (same SHA-256), and the three
v1 repositories do not exist, so those versions were running stock Whisper
under another name. v1.1.7 removes them from the model list. If your settings
name one of them, the matching Whisper model is used and files you already
downloaded are reused.

The Turkish datasets built for this project remain on Hugging Face:

- [sesmetin-v2-prtk-speech-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-prtk-speech-corpus)
- [sesmetin-v2-tdk-10m-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-tdk-10m-corpus)
- [sesmetin-v2-speech-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus)

The training and publishing scripts are in `tools/`.

## Roadmap

### Released
- [x] v1.0.4: first stable release.
- [x] v1.0.7: settings stored in `%APPDATA%\SesMetinPro`.
- [x] v1.1.0: model manager, hardware detection, installer.
- [x] v1.1.7: accuracy fixes, working updater, honest model list, measured
  benchmarks. Last feature release of the Python app.

### Next
- [ ] v2.0.0: the app rewritten in Rust with a Tauri interface. Same
  features, a new speaker-separation model, a signed one-click updater. The
  plan and its acceptance criteria are in [docs/PARITY.md](docs/PARITY.md)
  and [docs/adr/0001-rewrite-app-in-rust.md](docs/adr/0001-rewrite-app-in-rust.md).

### Ideas, not scheduled
- [ ] Batch queue for several files.
- [ ] Live microphone transcription.
- [ ] Custom vocabulary.

Full history: [CHANGELOG.md](CHANGELOG.md).

## License and mandatory visual attribution

This project is licensed under the **MIT License with a Mandatory Visual
Attribution Clause**.

Anyone using, embedding or modifying this source code, its components or its
algorithms in their own application must keep a **clearly visible, clickable
attribution link** to this repository
([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text))
on the **main screen or top menu bar** of their interface.

Hiding, obscuring or removing this visual attribution violates the license.

Full terms: [LICENSE](LICENSE).
Official repository: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
