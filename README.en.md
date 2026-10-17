<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Offline Speech-to-Text, Speaker Diarization, and Transcription System

[![Release](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=Release)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![License](https://img.shields.io/badge/License-MIT%20%2B%20Visual%20Attribution-F59E0B)](LICENSE)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Offline-10B981)](https://github.com/The0Sanity/Speech-To-Text)
[![UI](https://img.shields.io/badge/UI-Flet%20Flutter%20Native-0284C7)](https://flet.dev)
[![ASR Engine](https://img.shields.io/badge/ASR-Faster--Whisper%20INT8-8B5CF6)](https://github.com/SYSTRAN/faster-whisper)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## Overview

SesMetin Pro is a modern desktop application that converts audio and video recordings into text completely offline on your local computer, while automatically identifying and labeling different speakers (X1, X2, etc.) in the conversation.

No audio or transcript data is ever transmitted to external servers or cloud providers; your privacy is fully protected. The core pipeline is optimized with **CTranslate2 INT8** quantization to deliver responsive transcription and low memory consumption on standard consumer hardware (such as an Intel Core i3 with 8 GB RAM).

---

## Key Features

- **Windows 11 Fluent Dark UI:** Flutter GPU-accelerated desktop experience, skeleton shimmer loading transitions, and responsive window ergonomics.
- **100% Offline & Private:** All neural models run locally on your hardware with no internet required during transcription.
- **Audio Preprocessing Pipeline:** 80 Hz high-pass filter (cuts low-frequency rumble and plosives), intelligent noise gate, and peak loudness normalization for clean speech signals.
- **Smart Speaker Diarization:** Automatically detects and clusters distinct voices, providing a dedicated speaker management panel to rename participants.
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
- **Seamless Update Engine:** Checks for new releases via GitHub Releases upon application startup and inside the settings tab.

---

## Quick Start

### Option 1: Standalone Application (.exe) — Recommended

No installation or technical setup required:

1. Visit the [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases) page.
2. Download the latest `SpeechToText.exe` asset.
3. Double-click the downloaded executable to run the application immediately.

> [!NOTE]
> **Windows SmartScreen Notice:**
> When launching newly released open-source executables, Windows SmartScreen may display a *"Windows protected your PC"* dialog. This is a standard notification for newly built standalone applications. Click **"More info"**, then select **"Run anyway"** to launch. Our binaries are built without UPX compression, include complete PE version metadata, and are signed with an Authenticode certificate to ensure file integrity.

### Option 2: Run from Source

For developers or advanced users running from the source repository:

1. Clone or download this repository to your machine.
2. Double-click `run.bat` in the root directory.
   - The script automatically provisions the virtual environment (`venv`), installs dependencies, and launches the application.
3. Alternatively, launch directly via terminal:
   ```powershell
   python main.py
   ```

---

## Version Roadmap & TODO

Project development is organized into focused release milestones. The roadmap below tracks upcoming features up to version v2.0.0:

### v1.0.3 — Stable Foundation & Fast Launch (Current Release)
- [x] Standalone single-file `SpeechToText.exe` distribution (zero Python prerequisite).
- [x] Instant startup optimization with window priority elevation (eliminates background launch delays).
- [x] Flutter skeleton shimmer loading states for visual feedback.
- [x] Antivirus false-positive prevention (UPX eliminated, Authenticode signing, valid PE metadata).
- [x] Embedded FFmpeg bootstrapper (automatic provisioning when missing).
- [x] GitHub Releases auto-updater integration.

### v1.1.0 — Model Hub & Hardware Diagnostics (Planned)
- [ ] Visual Model Hub (one-click download, removal, and disk space management for Tiny, Base, Small, Medium models).
- [ ] Hardware Diagnostics (automatic detection of NVIDIA CUDA / cuDNN and CPU AVX2 with an in-app compute selector).
- [ ] Dual Distribution Channels (Portable standalone `.exe` alongside a standard Windows Setup installer).
- [ ] Batch Processing Queue (add multiple audio and video files to a processing queue for sequential transcription).

### v1.2.0 — Real-Time Live Speech & Desktop Subtitles (Planned)
- [ ] Live Microphone Input (real-time live speech-to-text during meetings, lectures, and calls).
- [ ] Desktop Floating Subtitle Bar (transparent, always-on-top overlay for system-wide live captions).
- [ ] Silero VAD Semantic Chunking (pause-based 400ms segmentation to prevent mid-sentence cuts).
- [ ] Custom Phonetic Hotwords & Glossary (custom dictionary injection for industry-specific terminology and abbreviations).

### v2.0.0 — Enterprise Speech Intelligence & Local LLM Summaries (Target Release)
- [ ] Cross-Lingual Live Translation (direct real-time translation of spoken Turkish to English, German, French, and Spanish).
- [ ] Persistent Cross-Session Speaker Recognition (store speaker voiceprints to automatically identify known participants in future sessions).
- [ ] Native Video Hardsubbing Engine (burn subtitles directly into MP4 video with custom styling).
- [ ] Zero-Cloud Local LLM Meeting Summary (fully offline AI generation of executive summaries, decisions, and action items).

---

## License & Mandatory Visual Attribution

This project is licensed under the **MIT License with Prominent Visual Attribution Requirement**.

### Mandatory Visual Attribution Rule:
Any individual, organization, or project using this software, its source code, algorithms, or derivative works is strictly required to include a prominent, clickable visual attribution (link or badge) directing to this repository ([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)) on the **main screen or primary top navigation bar** of their user interface.

Hiding, obscuring, or burying this attribution in submenus, settings drawers, or hidden footers constitutes a violation of the license terms.

For complete legal terms, review the [LICENSE](LICENSE) file.  
Repository: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
