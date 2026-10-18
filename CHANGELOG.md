# Changelog

All notable changes to the **SesMetin Pro (Speech-To-Text)** project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added / Yenilikler
- **10M+ Turkish TDK Permutation Corpus Pipeline / 10 Milyon+ TDK Kelime Permutasyon Veri Hatti**:
  - Engineered combinatorial permutation generator using the official Turkish Language Association (TDK 12th Edition, 81,700+ headwords) lexicon.
  - Implemented hybrid distribution with 70% natural punctuation (capitalization, commas, periods across 4-25 words) and 30% unpunctuated lowercase acoustic token streams.
  - Built zero-local-disk streaming Parquet serialization with PyArrow and direct memory upload to Hugging Face Datasets (`The0Sanity/sesmetin-v2-tdk-10m-corpus`).
  - Added standalone PEP 723 cloud job runner (`tools/huggingface/cloud_tdk_10m_job.py`) for 100% cloud-based execution via `hf jobs uv run`.
  - Upgraded `tools/huggingface/hf_train_job.py` with streaming dataset support (`streaming=True`) for high-throughput training directly from Hugging Face Hub.

## [v1.1.0] - 2026-10-18

### Added / Yenilikler
- **Intelligent Hardware Acceleration & Mode Selection / Akilli Donanim Hizlandirma ve Kip Secimi**:
  - Added multi-tier execution modes: `Auto (Otomatik - Onerilen)`, `NVIDIA CUDA GPU Hizlandirma`, and `CPU INT8 (AVX2 Vektor Hizlandirma)`.
  - Automatic fallback to CPU INT8 if CUDA is unavailable or if device memory is exceeded.
  - Dynamically configures CTranslate2 execution device and compute type (`cuda/float16` vs `cpu/int8`).
- **Real-Time Performance & Memory HUD / Gercek Zamanli Donanim ve Bellek Paneli**:
  - Added reactive performance HUD displaying required model RAM and VRAM alongside live system memory availability.
  - Color-coded compatibility status badge (`Tam Uyumlu` in green, `Sistem Sinirinda` in amber) with contextual warning notifications for low RAM/VRAM situations.
  - Instant live recalculation when switching between models or hardware acceleration modes.
- **Model Catalog Completion (large-v3) / Model Katalogu Tamamlama**:
  - Added official OpenAI `large-v3` flagship model (1550M parameters, ~3.1 GB) with full CTranslate2 INT8 quantization to both the Model Hub and the transcription dropdown selector.
- **Dual Packaging Format / Cift Paketleme Formati**:
  - Introduced official Inno Setup installer script (`packaging/installer.iss`) producing `SpeechToText-Setup.exe` with Start Menu integration, desktop shortcuts, and clean uninstaller.
  - Retained standalone portable executable (`SpeechToText.exe`) for zero-installation portable usage.
- **Enhanced Release Automation / Gelismis Surum Is Akisi**:
  - GitHub Actions release workflow updated to automatically compile, sign, verify, and publish both Portable and Setup executables with dedicated SHA-256 checksums.

### Fixed / Duzeltmeler
- **Dropdown Event Compatibility / Acilir Menu Olay Uyumlulugu**:
  - Ensured seamless event binding across Flet framework updates using `on_select` callback handlers.
- **Model Compatibility Precision / Model Uyumluluk Hesaplamalari**:
  - Integrated dynamic memory threshold heuristics for system boundary analysis, preventing out-of-memory crashes on resource-constrained workstations.

## [v1.0.9] - 2026-10-18

### Added / Yenilikler
- **Silent Native PowerShell Self-Updater Engine / Sessiz PowerShell Guncelleyici**:
  - Replaced legacy batch script execution with fully hidden PowerShell self-update engine (`generate_powershell_script`).
  - Executes with `-WindowStyle Hidden`, `CREATE_NO_WINDOW`, and `DEVNULL` standard streams, completely eliminating command prompt windows and console popups.
  - Implemented 30-attempt safe file-swap loop with 500ms intervals and automatic `.bak` backup and rollback on any filesystem contention.
  - Safely handles PyInstaller parent/child process architectures by identifying and gracefully terminating related process trees before file replacement.
- **Thread-Safe Modal Progress Synchronization / Guvenli Arayuz Ilerleme Senkronizasyonu**:
  - Integrated `_dispatch_ui` using `page.run_task` and `page.update()` to reliably push WebSocket state updates to Flet modal dialogs.
  - Guaranteed visual transition to 100% completion before executing the silent restart sequence.
- **Turkish Synthetic Dialogue & Longform Audio Generators / Sentetik Turkce Diyalog Ureticisi**:
  - Integrated local Kokoro-82M model support and multi-speaker Turkish dialogue generators for realistic telephony, cashier, fast-speech, and longform audio synthesis.
  - Built non-repeating test generation pipelines producing 5-10 minute audio files for stress testing and model evaluation.
- **SesMetin v2 Benchmark Evaluation / SesMetin v2 Basarim Olcumleri**:
  - Evaluated acoustic preprocessing, ITN, and Whisper inference across non-repeating Turkish datasets, achieving 0.38% Mean WER and 100% ITN accuracy.
- **GitHub Community Standards & SEO Infrastructure / Topluluk ve SEO Altyapisi**:
  - Added structured GitHub Issue templates (`bug_report.yml`, `feature_request.yml`), Pull Request template, `CONTRIBUTING.md`, and `SECURITY.md`.
  - Configured 20 targeted discoverability topics on GitHub for improved Explore and Search indexing.

### Fixed / Duzeltmeler
- **Start Transcription UI Crash / Transkripsiyon Baslatma Arayuz Hatasi**:
  - Fixed `AttributeError: 'FletSpeechToTextApp' object has no attribute 'transcript_column'` triggered when clicking the green start button by referencing `self.transcript_list` and maintaining `self.transcript_column` backwards-compatibility alias.
  - Implemented automatic reset of transcript view to clean placeholder if transcription is cancelled or errors occur during execution.
- **Command Prompt Popup & Hang / Komut Istemi Penceresi ve Kilitlenme**:
  - Completely resolved the issue where an empty command prompt window titled `Find {pid_number}` popped up and hung indefinitely during self-update.
- **Update Modal Progress Freeze / Guncelleme Cubugu Donma Hatasi**:
  - Fixed background thread race condition where update modal progress would visually freeze around ~72% due to dropped WebSocket frames on secondary threads.

### Cloud Training & Datasets / Bulut Egitimi ve Veri Setleri
- **Hugging Face Cloud Training Pipeline / Hugging Face Bulut Egitim Hatti**:
  - Offloaded all model fine-tuning and heavy compute to Hugging Face Cloud Jobs GPU infrastructure (`tools/huggingface/hf_train_job.py`, `tools/huggingface/launch_cloud_training.py`).
  - Added safeguards against local workstation compute degradation (`--allow-local-compute` guard).
  - Published Turkish speech corpus to Hugging Face Datasets (`The0Sanity/sesmetin-v2-speech-corpus`).
  - Published and verified `The0Sanity/sesmetin-v2-tiny-ct2` CTranslate2 model on Hugging Face Hub.

### Security & Build / Guvenlik ve Derleme
- **Painless Self-Update Execution / Guvenli Yerinde Guncelleme**:
  - Subprocess spawned with detached process groups and no window allocation, preventing user interruption and ensuring atomic binary swapping.
- **Authenticode Signature & Integrity Verification**:
  - Standalone release binaries (`SpeechToText.exe`) signed with Authenticode certificates and verified via SHA256 checksums (`SpeechToText.exe.sha256`).

---

## [v1.0.7] - 2026-10-17

### Added / Yenilikler
- **OS-Standard Configuration Storage / Standart Yapilandirma Dizini**:
  - Relocated settings from loose `settings.json` in the executable folder to OS-standard user profile directory (`%APPDATA%\SesMetinPro\config.json` on Windows, `~/.config/sesmetinpro/config.json` on Unix).
  - Automatically migrates existing settings and deletes the legacy `settings.json` file to keep the application directory clean and clutter-free.
- **Markdown Rendering in Patch Notes Modal / Surum Notlarinda Markdown Destegi**:
  - Implemented scrollable `ft.Markdown` rendering in the update notification dialog with selectable text, preserving headers, lists, code blocks, and formatting.

### Changed / Degisiklikler
- **Minimalist Window and Header Title / Minimalist Baslik**:
  - Simplified application title bar and main window header strictly to `"SesMetin Pro"`, eliminating secondary subtitle clutter while retaining the official GitHub attribution link.
- **Synchronized Version Metadata / Surum Senkronizasyonu**:
  - Synchronized version `1.0.7` across `src/config.py`, `src/__init__.py`, and Windows PE metadata `version_info.txt`.

### Fixed / Duzeltmeler
- **Auto-Updater Process Deadlock / Guncelleme Surec Kilitlenmesi**:
  - Resolved deadlock where background threads kept the process alive after downloading updates by utilizing `os._exit(0)` when spawning the updater batch script.
- **Update Dialog Button Toggles / Guncelleme Buton Durumlari**:
  - Corrected button visibility transitions during active downloads, ensuring cancel and update buttons toggle smoothly without frozen states.

---

## [v1.0.6] - 2026-10-17

### Added / Yenilikler
- **Smooth Throttled Progress Bar / Akici Ilerleme Cubugu**:
  - Implemented 80ms interval throttling (~12 FPS) to eliminate Flet WebSocket IPC bridge congestion during large binary downloads.
  - Added exponential moving average download speed calculation in MB/s and intelligent countdown estimated time of arrival (ETA).
  - Enforced targeted control updates (`_safe_update`) to prevent full-page DOM reconciliation on download progress ticks.
- **Postponed Update Memory / Ertelenmis Guncelleme Hatirlatma**:
  - Selecting "Daha Sonra" (Later) or closing the update dialog persists the release metadata into `settings.json`.
  - On next application startup, the update dialog is automatically re-prompted without requiring a fresh network call.
- **Post-Update Patch Notes Modal / Acilista Surum Notlari Penceresi**:
  - Automatically displays rich Markdown release notes upon the updated executable's first launch.
  - Includes a selectable, scrollable GitHub Markdown dialog with feature overview and verification notes.

### Fixed / Duzeltmeler
- Eliminated UI freezing and WebSocket buffer dropouts during high-speed release downloads.

---

## [v1.0.5] - 2026-10-17

### Fixed / Duzeltmeler
- **Updater HTTP 304 Handling / Guncelleyici HTTP 304 Hatasi**:
  - Resolved GitHub API `HTTP 304 Not Modified` exception when checking updates with cached ETags.
  - Gracefully treats HTTP 304 as up-to-date status and refreshes cache headers.
- **Window Opacity and Transparency Glitch / Pencere Seffaflik Sorunu**:
  - Enforced window opacity 1.0 on launch to prevent DWM composition from rendering the desktop app at 50% opacity.
- **FFmpeg Resolution Fallback / FFmpeg NameError**:
  - Fixed `NameError: find_ffmpeg` in audio extraction fallback paths.
- **YouTube Media Extraction / YouTube Demet Cozme Hatasi**:
  - Fixed tuple unpacking error when extracting media info from single-stream sources.
- **Speaker Diarization Pitch Estimation / Konusmaci Ayristirma Hizi**:
  - Optimized pitch calculation from $O(N^2)$ to $O(N)$ with downsampled peak-picking.
- **Turkish Inverse Text Normalization (ITN) / Turkce Sayi ve Metin Normalizasyonu**:
  - Fixed case sensitivity in number and currency word replacement algorithms.

### Documentation / Dokumantasyon
- Expanded version roadmap in `README.md` covering upcoming milestones v1.3.0 to v2.0.0.

---

## [v1.0.4] - 2026-10-17

### Fixed / Duzeltmeler
- **Flet Material Icons Asset Missing / Flet Ikon Paketi Eksikligi**:
  - Bundled missing `flet/controls/material/icons.json` asset into PyInstaller standalone specification.
  - Added runtime self-healing fallback that initializes a clean JSON fallback if assets are missing on the target host.
- **Offline Client Runtime / Cevrimdisi Calisma Zamani**:
  - Ensured standalone executable boots cleanly on systems without existing Python or Flet cache directories.

### Documentation / Dokumantasyon
- Comprehensive overhaul of `README.md` featuring bilingual English/Turkish toggle, SVG feature badges, architecture diagram, and release tracking.

---

## [v1.0.3] - 2026-10-17

### Security & Performance / Guvenlik ve Performans
- **Antivirus False-Positive Mitigation / Antivirus Uyari Temizligi**:
  - Eliminated UPX compression to remove heuristic false-positive alerts across antivirus engines (clean VirusTotal and Kaspersky scans).
- **Windows PE Metadata Embedding / Windows PE Dosya Bilgileri**:
  - Embedded genuine Windows PE `VersionInfo` metadata (FileVersion, ProductVersion, CompanyName, LegalCopyright).
- **Authenticode Code Signing / Kod Imzalama**:
  - Added automated Authenticode code signing with Digicert timestamping to the GitHub Actions release workflow.
- **Instant Foreground Startup / Hizli Acilis**:
  - Implemented lazy importing for heavy AI libraries (`torch`, `faster_whisper`), reducing application launch time from >12s to ~1.2s.
  - Forced foreground window focus on startup to prevent the application from opening minimized or in the background.

---

## [v1.0.2] - 2026-10-17

### Fixed / Duzeltmeler
- **Flet Desktop Module Import / flet_desktop Import Hatasi**:
  - Resolved `ModuleNotFoundError: flet_desktop` by embedding the desktop client runtime archive into the package.
- **Defensive Exit Handler / Guvenli Cikis Yoneticisi**:
  - Replaced unhandled `exit()` calls with defensive `_safe_exit()` to prevent runtime NameError on unexpected process exit.

---

## [v1.0.1] - 2026-10-17

### Fixed / Duzeltmeler
- **UnitTest Bundling Dependency / unittest Bagimliligi**:
  - Resolved `ModuleNotFoundError: unittest` caused by NumPy testing package dependencies in standalone PyInstaller packaging.
- **Windowed Standard Input / Konsolsuz Giris Hatasi**:
  - Fixed `RuntimeError: lost sys.stdin` in windowed executable mode with defensive stream fallback.

### Added / Yenilikler
- **In-App FFmpeg Bootstrapper / Otomatik FFmpeg Kurucusu**:
  - Added automated detection, download, and extraction helper for systems without FFmpeg installed.
- **Crash Logging / Hata Gunluk Kaydi**:
  - Added unhandled exception logging to `crash.log` in the application directory.

---

## [v1.0.0] - 2026-10-17

### Initial Release / Ilk Kararli Surum
- **100% Offline Speech Recognition / Yerel Ses Tanima**:
  - Fast, private Turkish speech-to-text powered by CTranslate2 and Faster-Whisper.
- **Acoustic Speaker Diarization / Konusmaci Ayristirma**:
  - Multi-speaker segmentation with turn merging, speaker labeling, and time offsets.
- **Audio Pre-Processing / Ses On-Isleme**:
  - 80Hz high-pass filter, noise reduction, and peak normalization.
- **YouTube Media Integration / YouTube Medya Aktarimi**:
  - Integrated yt-dlp media downloader for direct processing of online videos and audio.
- **Multi-Format Export / Coklu Disa Aktarim**:
  - Export transcripts to SRT, VTT, JSON, CSV, Markdown, and TXT with timestamps.
- **Built-in Auto-Updater / Dahili Guncelleyici**:
  - In-app release checking and binary downloads with PE integrity verification.
- **Prominent Visual Attribution / Gorsel Atif Bildirimi**:
  - Licensed under the MIT License with Prominent Visual Attribution Requirement to https://github.com/The0Sanity/Speech-To-Text.
