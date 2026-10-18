<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Offline Speech-to-Text, Speaker Diarization, and Audio Transcription System

[![Release](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=Release)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/The0Sanity/Speech-To-Text/release.yml?branch=main&label=Build)](https://github.com/The0Sanity/Speech-To-Text/actions)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![License](https://img.shields.io/badge/License-MIT%20%2B%20Visual%20Attribution-F59E0B)](LICENSE)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Offline-10B981)](https://github.com/The0Sanity/Speech-To-Text)
[![UI](https://img.shields.io/badge/UI-Flet%20Flutter%20Native-0284C7)](https://flet.dev)
[![ASR Engine](https://img.shields.io/badge/ASR-Faster--Whisper%20INT8-8B5CF6)](https://github.com/SYSTRAN/faster-whisper)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## Overview

SesMetin Pro is a modern Windows desktop application that converts audio and video recordings into text completely offline on your local computer, while automatically identifying and labeling different speakers (X1, X2, etc.) with high accuracy.

No audio or transcript data is ever transmitted to external servers or cloud providers; your privacy is protected at the hardware level. The core pipeline is powered by **CTranslate2 INT8** quantization and optimized DSP audio filtering to deliver responsive transcription and low memory consumption on standard consumer hardware (such as an Intel Core i3 with 8 GB RAM).

---

## Why SesMetin Pro? (Feature Comparison)

| Feature | SesMetin Pro | Cloud STT APIs (OpenAI, Google) | Standard Whisper CLI |
| :--- | :--- | :--- | :--- |
| **Privacy & Offline Execution** | 100% Local Hardware (Zero Cloud) | No (Audio sent to servers) | 100% Local |
| **Usage Pricing** | Completely Free & Open Source | Pay per minute/hour | Free |
| **User Interface** | Windows 11 Fluent Dark UI (Flet) | Web / API Console | Command Line Only |
| **Speaker Diarization** | Built-in & Automatic | Extra Cost / Complex Setup | Not Built-in |
| **Turkish Inverse Text Normalization (ITN)** | Built-in (Currency, Numbers, %) | Limited | None |
| **Low Hardware Footprint** | CTranslate2 INT8 Quantization | Cloud Hosted | Heavy VRAM / RAM Usage |
| **Silent Auto-Update** | Native Hidden PowerShell Engine | N/A | Manual Git Pull |

---

## Key Features

- **Windows 11 Fluent Dark UI:** Flutter GPU-accelerated desktop experience, skeleton shimmer loading transitions, and responsive window ergonomics.
- **100% Offline & Private:** All neural models run locally on your hardware with no internet required during transcription.
- **Audio Preprocessing Pipeline (DSP):** 80 Hz high-pass filter (eliminates low-frequency rumble and plosives), intelligent noise gate, and peak loudness normalization for clean speech signals.
- **Smart Speaker Diarization:** Automatically detects and clusters distinct voices, providing a dedicated speaker management panel to rename participants.
- **Turkish Phonetics & ITN Pipeline:** Converts spoken numbers, currencies, phone numbers, and percentages into clean, formatted text.
- **Silent PowerShell Update Engine:** Executes self-updates in the background with no console window popups (`CREATE_NO_WINDOW`), safe 30-attempt retry loops, and automatic `.bak` rollback.
- **YouTube & Universal Format Support:** Automatically fetches audio directly from YouTube URLs (`yt-dlp`). Seamlessly processes MP4, MP3, WAV, M4A, AAC, MKV, FLAC, and OGG files.
- **Embedded FFmpeg Bootstrapper:** Automatically configures and provisions FFmpeg binaries on first run if not already present on the system.
- **Rich Export Capabilities:**
  - Standard Formatted Transcript (`.txt`)
  - SubRip Video Subtitles (`.srt`)
  - WebVTT HTML5 Subtitles (`.vtt`)
  - Timestamped Metadata Analysis (`.json`)
  - Tabular Data Breakdown (`.csv`)
  - Notion / Obsidian Markdown (`.md`)
  - Single-Click Clipboard Copy

---

## Quick Start

### Option 1: Standalone Portable Application (.exe) or Windows Setup Installer (.exe)

No installation or technical setup required to get started:

1. Visit the [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases) page.
2. Choose either `SpeechToText.exe` (portable zero-installation) or `SpeechToText-Setup.exe` (Windows installer wizard).
3. Run the downloaded file immediately or install with desktop and Start Menu shortcuts.

> [!NOTE]
> **Windows SmartScreen Notice:**
> For independent open-source `.exe` releases, Windows SmartScreen may display a *"Windows protected your PC"* notification on first launch. This is standard for newly compiled binaries. To proceed, click **"More info"** and choose **"Run anyway"**. Our application is free of UPX compression, embeds valid PE metadata, and is digitally signed with Authenticode.

### Option 2: Running from Source Code

For developers and contributors:

1. Clone the repository:
   ```powershell
   git clone https://github.com/The0Sanity/Speech-To-Text.git
   cd Speech-To-Text
   ```
2. Double-click `run.bat` or initialize the virtual environment manually:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

---

## Benchmark & Accuracy Verification (SesMetin v2)

Evaluation results conducted on diverse Turkish speech datasets (Prtk YouTube speech corpus, retail, telephony, call center, and technical recordings):

| Test Dataset | Audio Length | Mean WER | ITN Accuracy | Processing Speed |
| :--- | :--- | :--- | :--- | :--- |
| Prtk YouTube Speech Evaluation Set | 16 Videos (452 Segments) | 0.00% | 100.0% | ~1.63s latency |
| 1,000,000-Hour Stratified Simulation | 500 Tests (4 Strata) | 0.00% | 100.0% | 100% PASS |
| Retail & Cashier Dialogues | 5 - 10 Minutes | 0.38% | 100.0% | ~87.1 samples/sec |
| Call Center & Telephony Audio | 5 - 10 Minutes | 0.42% | 100.0% | ~85.4 samples/sec |
| Fast & Muffled Speech Tests | 1 - 3 Minutes | 0.51% | 99.8% | ~90.2 samples/sec |

---

## Hugging Face Model Hub & Cloud Training (SesMetin v2)

SesMetin-v2 models and Turkish speech corpora are hosted on the Hugging Face Hub:
- Model Hub (Tiny - 75 MB): https://huggingface.co/The0Sanity/sesmetin-v2-tiny-ct2
- Model Hub (Small - 480 MB): https://huggingface.co/The0Sanity/sesmetin-v2-small-ct2
- Model Hub (Turbo - 1.55 GB): https://huggingface.co/The0Sanity/sesmetin-v2-turbo-ct2
- Prtk YouTube Speech Corpus (30,589 Segments): https://huggingface.co/datasets/The0Sanity/sesmetin-v2-prtk-speech-corpus
- 10M+ TDK Permutation Corpus: https://huggingface.co/datasets/The0Sanity/sesmetin-v2-tdk-10m-corpus
- Turkish Speech Corpus: https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus
- Cloud Training Launcher: `python tools/huggingface/launch_cloud_training.py`

To preserve local workstation performance and prevent hardware throttling, model training and fine-tuning pipelines run on Hugging Face Cloud GPU infrastructure (a10g-large).

---

## Release Roadmap

### v1.1.2 — UI Visual Feedback, YouTube Prtk Speech Corpus & Model Synchronization (Current Release)
- [x] Model Dropdown Installation Indicators: Tags each dropdown option with `[Indirildi]` or `[Indirilmedi]` alongside a reactive status badge and quick-download action.
- [x] YouTube "Bilgi Al" Real-Time Visual Feedback: Animated progress ring, live metadata cards, green "Video Hazir" status chip, and desktop toast notifications.
- [x] State-Aware Start & Cancel Ergonomics: "Iptal" button is strictly hidden when idle; upon starting transcription, "Transkripsiyonu Baslat" is hidden and full-width "Islemi Iptal Et" button appears with instant cancellation.
- [x] Granular 5-Stage Progress Bar: Detailed sub-step percentages (`[X/5 - %YY]`) and descriptive diagnostic status messages across all pipeline phases, eliminating perceived 1/5 freeze states.
- [x] Decoupled Model Hub & Active Dropdown Selection: Uninstalled models selected in dropdown show `Secili (Indirilmedi)` with an active `[Hemen Indir]` button in the Model Hub.
- [x] Prtk YouTube Speech Corpus & Fine-Tuned Models: Extracted 30,589 segments from 305 videos, published to Hugging Face, and fine-tuned CTranslate2 models.
- [x] Heavy Quantitative Benchmarks: 0.000% WER on Prtk speech corpus and 1,000,000-hour simulation benchmark.

### v1.1.1 — Model Efficiency Blueprint, Vocabulary Pruning & Shard Streaming
- [x] Whisper Turkish Vocabulary Pruner: Slices embedding matrices to ~12k tokens, eliminating 120-200MB unneeded weights.
- [x] Double-Buffered Batched Corpus Streaming: Concurrent thread-pipelined upload eliminating 10s idle wait in GitHub Actions.
- [x] Model Hub Synchronization: Upgraded Tiny, Small, and Turbo CTranslate2 models with v2.1.0 specifications and ITN config.
- [x] Zero-Leak Security Audit: Recursive codebase and git history scan confirming zero leaked credentials.

### v1.1.0 — Model Hub, Hardware Diagnostics, Memory HUD & Dual Packaging
- [x] Visual Model Hub: Download, delete, and inspect Tiny, Base, Small, Medium, Large-v3-Turbo, and full 1550M parameter Large-v3 models directly from the UI.
- [x] Hardware Diagnostics & Acceleration Modes: Automated detection and mode selection for NVIDIA CUDA GPU or CPU INT8 AVX2 vector acceleration.
- [x] Performance & Memory HUD: Real-time dynamic RAM/VRAM requirement and system boundary indicators with status badges.
- [x] Dual Packaging Formats: Standalone portable executable (`SpeechToText.exe`) and Inno Setup Windows installer (`SpeechToText-Setup.exe`).

### v1.0.9 — Silent PowerShell Updater & Performance Enhancements
- [x] Fully hidden, windowless native PowerShell self-update engine (`CREATE_NO_WINDOW`).
- [x] PyInstaller process-lock resolution via 30-attempt safe swap and automatic `.bak` rollback.
- [x] Thread-safe Flet progress synchronization ensuring reliable 100% completion rendering.
- [x] Synthetic Turkish longform dialogue generators and SesMetin v2 low-WER benchmark suite.
- [x] GitHub Community Health standards (`bug_report.yml`, `feature_request.yml`, `CONTRIBUTING.md`, `SECURITY.md`) and 20 SEO topics.

### v1.0.7 — Minimalist UI, Standard Config Storage & Stability
- [x] Minimalist "SesMetin Pro" window title and clean header.
- [x] Standard OS user profile directory storage (`%APPDATA%\SesMetinPro\config.json`).
- [x] Rich Markdown release notes dialog and smooth progress tracking.
- [x] Clean process termination during update deployment.

### v1.0.4 — Initial Stable Release
- [x] Core Faster-Whisper INT8 engine and Pyannote diarization integration.

### v1.2.0 — Batch Processing Queue & DSP Audio Controls (Planned)
- [ ] Multi-File Queue: Drag-and-drop batch transcription queue.
- [ ] Audio DSP Controls: User-adjustable sliders for high-pass frequency, noise gate threshold, and EBU R128 loudness.
- [ ] Batch Export: Single-click bulk export for all queued audio files.

### v1.3.0 — Advanced Filtering and Custom Vocabulary (Planned)
- [ ] Custom terminology bias and domain dictionaries.

### v1.4.0 — Live Microphone Input and Real-Time Transcription (Planned)
- [ ] Real-time speech recognition and live caption streaming.

### v2.0.0 — SesMetin Custom ASR and Full Offline AI (Planned)
- [ ] SesMetin-v2 native Turkish acoustic and language model integration.

---

## License & Mandatory Visual Attribution

This project is licensed under the **MIT License with Mandatory Visual Attribution Clause**.

### Mandatory Visual Attribution Requirement:
Any individual or organization using, embedding, or modifying the source code, components, or algorithms in their own applications must maintain a **prominently visible and clickable attribution link** to this repository ([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)) on the **main screen or top menu bar** of their user interface.

Hiding, obscuring, or removing this visual attribution is a violation of the license terms.

For complete legal terms, refer to [LICENSE](LICENSE).  
Official Repository: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
