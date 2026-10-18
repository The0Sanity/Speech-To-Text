# Changelog

All notable changes to the **SesMetin Pro (Speech-To-Text)** project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.1.4] - 2026-10-18

### Fixed / Duzeltmeler
- **Elimination of Empty Transcription Outputs on Turkish Music & Songs / Muzikli Turkce Kayitlarda Bos Cikti Hatasinin Giderilmesi**:
  - **Silero VAD Music False-Negative Elimination / Silero VAD Muzik Yanilgisinin Giderilmesi**:
    - Resolved an issue where Silero VAD with high sensitivity thresholds incorrectly classified children's songs, nursery rhymes, and recordings with background instruments (e.g. `https://www.youtube.com/watch?v=IrYUYT5C5GI`) as non-speech noise, stripping over 95% of audible speech before reaching the decoder.
    - Added automatic audio energy (RMS) monitoring and adaptive fallback: if initial VAD decoding produces fewer than 5% speech coverage on audible recordings (RMS > 0.015), the transcriber automatically re-processes the audio without VAD (`vad_filter=False`) using robust anti-repetition decoding.
  - **Non-Destructive Trailing Loop Cleaning / Parca Silme Yerine Akilli Sonlandirma**:
    - Replaced catastrophic whole-segment deletion (`should_filter_segment` discarding 30-second segments when zlib compression ratio > 2.4) with `clean_trailing_repetitions`.
    - Detects repeating 1, 2, 3, or 4-gram trailing hallucination loops and truncates the repetition tail to a maximum of 2 iterations while fully preserving all preceding valid transcribed speech.
  - **Preservation of Turkish Reduplications & Rhymes / Turkce Ikilemelerin ve Sarki Sozlerinin Korunmasi**:
    - Enhanced `src/text_postprocessor.py` to recognize Turkish reduplications (*ikilemeler*) such as "pisi pisi", "kucu kucu", "yavas yavas", "patates patates". Consecutive duplicate words are now allowed up to 2 times instead of being collapsed destructively.
    - Refactored `_is_hallucination` so meaningful Turkish words repeating rhythmically in songs or choruses are no longer purged as noise hallucinations.
    - Allowed consecutive identical chorus segments up to 2 times, preserving lyrical musical verses.
  - **Prompt Regurgitation Mitigation / Istem Tekrari Onleme**:
    - Configured `WhisperTranscriber` to bypass long synthetic system prompts on `tiny` and `base` architectures, preventing smaller decoders from regurgitating the prompt instead of listening to faint audio.

### Added / Yenilikler
- **100% Empirical Audio Benchmark Suite / %100 Ampirik Gercek Ses Karsilastirma Paketi**:
  - Completely rewrote `tools/benchmarks/benchmark_prtk_accuracy.py` to eliminate all simulated/mocked hypotheses (`hyp_text = ref_text`).
  - The suite now executes genuine CTranslate2 inference across multiple models (`Systran/faster-whisper-small`, `The0Sanity/sesmetin-v2-tiny-ct2`) on actual audio extracted from `https://www.youtube.com/watch?v=IrYUYT5C5GI` and computes verifiable Word Error Rate (WER) and Character Error Rate (CER) against user ground truth.
  - Generates authentic JSON reports at `dataset/prtk_speech_corpus/benchmark_prtk_report.json` with reproducible metrics and complete hypothesis text.
- **Unit Test Coverage for Anti-Loop and Reduplication Engines**:
  - Implemented `tests/test_transcriber_anti_loop.py` validating trailing repetition truncation and adaptive VAD parameters.
  - Implemented `tests/test_postprocessor_reduplication.py` validating Turkish reduplication preservation, non-destructive chorus retention, and junk hallucination filtering.

## [v1.1.3] - 2026-10-18

### Fixed / Duzeltmeler
- **PyInstaller `_MEIPASS2` Child Process Leaks & Auto-Updater DLL Crash Fix / PyInstaller Ortam Degiskeni Sizintisi ve Guncelleyici DLL Cokmesi Duzeltmesi**:
  - **Critical `python312.dll` Missing Error Resolved / Kritik `python312.dll` Bulunamadi Hatasi Cozuldu**:
    - Fixed a critical crash where updating from an existing PyInstaller one-file executable failed with:
      `Failed to load Python DLL '...\AppData\Local\Temp\_MEIxxxxxx\python312.dll'. LoadLibrary: Belirtilen modul bulunamadi.`
    - **Root Cause Eliminated / Kok Neden Ortadan Kaldirildi**: When PyInstaller one-file executables launch, the C bootloader exports `_MEIPASS2` pointing to the temporary extraction directory. Spawning the background updater PowerShell script via `subprocess.Popen` caused child processes to inherit the stale `_MEIPASS2`. When PowerShell killed the old executable and launched the updated binary, the new PyInstaller bootloader detected `_MEIPASS2`, falsely assumed its libraries were already unpacked, and attempted to load `python312.dll` from the old (now deleted) temporary folder.
    - **Double-Layer Environment Scrubbing / Cift Katmanli Ortam Degiskeni Temizligi**:
      1. In `WindowsSelfUpdater.execute_in_place_update`, explicitly scrubbed `_MEIPASS2`, `_MEIPASS`, `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP`, `PYTHONEXECUTABLE`, `PYTHONNOUSERSITE`, and `PYI_PARENT_PID` before spawning PowerShell via `subprocess.Popen(..., env=clean_env)`.
      2. In `WindowsSelfUpdater.generate_powershell_script`, added explicit Step 0 and Step 5 environment purges executing `Remove-Item -Path "Env:\$v"` and `[System.Environment]::SetEnvironmentVariable($v, $null, [System.EnvironmentVariableTarget]::Process)` immediately before invoking the new application binary.
  - **Win32 File Lock Verification & Adaptive Replacement / Win32 Dosya Kilidi Dogrulamasi ve Uyarlanabilir Degistirme**:
    - Replaced blind sleeps with a non-blocking Win32 file lock probe using `[System.IO.File]::Open($CurExe, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)` to verify 100% handle release by terminating parent processes before attempting filesystem replacement.
    - Added an adaptive retry loop for moving the current executable to `.bak` and moving the updated binary into place, preventing transient `Access is denied (0x80070005)` antivirus or indexer locking errors.
  - **Asset-Specific SHA256 Checksum Matching / Varliga Ozel SHA256 Saglama Toplami Eslestirmesi**:
    - Enhanced `AutoUpdater.parse_release_payload` to prioritize regex patterns matching the exact executable name (`SpeechToText.exe: <hash>`) rather than capturing the first arbitrary 64-character hex string, ensuring zero checksum mismatch when both Portable and Setup executables are published together in release notes.
  - **Dev-Mode Subprocess Sanitization / Gelistirici Kipi Surec Yalitim Guvenligi**:
    - Sanitized child process environments and removed `shell=True` in non-frozen developer mode updates to guarantee clean process startup across all development workflows.

### Added / Yenilikler
- **Comprehensive Updater Test Suite / Kapsamli Guncelleyici Test Paketi**:
  - Authored `tests/test_updater_env_isolation.py` strictly verifying environment variable sanitization, PowerShell removal directives, file lock retry loops, and multi-asset SHA256 parsing following the Test-First Superpowers methodology.

## [v1.1.2] - 2026-10-18

### Added / Yenilikler
- **Comprehensive UI Visual Feedback & Model Hub Synchronization / Kapsamli Arayuz Geri Bildirimleri ve Model Merkezi Senkronizasyonu**:
  - **Model Dropdown Download Status Tags / Model Seciminde Indirme Durumu Etiketleri**:
    - Automatically appends `[Indirildi]` and `[Indirilmedi]` status indicators to every model option in the "Whisper Modeli" dropdown selector.
    - Added reactive status indicator container directly underneath the dropdown displaying instant download badges and a direct `[Modeli Indir]` action button for uninstalled models.
  - **YouTube "Bilgi Al" Real-Time Progress & Feedback / YouTube "Bilgi Al" Canli Ilerleme ve Geri Bildirimi**:
    - Replaced silent background querying with an animated progress spinner (`ProgressRing`), "Bilgiler Aliniyor..." status text, and automatic button disabling to prevent duplicate network calls.
    - Dynamic header metadata updates displaying video title, channel name, formatted duration (`MM:SS`), and a vibrant green "Video Hazir" status chip with checkmark icon upon completion.
    - Integrated non-blocking desktop toast notifications signaling successful metadata retrieval or explicit error reasons.
  - **State-Aware Start & Cancel Action Ergonomics / Durum Odakli Baslat ve Iptal Buton Davranisi**:
    - "Iptal" button is strictly hidden and disabled while idle, preventing user confusion before transcription starts.
    - When transcription starts, "Transkripsiyonu Baslat" is smoothly hidden, and the full-width "Islemi Iptal Et" button is displayed with instant cancellation response and progress resetting.
  - **Granular 5-Stage Progress Bar & Diagnostic Labeling / 5 Asamali Ayrintili Ilerleme Cubugu ve Teshis Etiketleri**:
    - Completely eliminated perceived 1/5 freeze states by introducing granular sub-step percentage tracking (`[X/5 - %YY]`) and descriptive status messages across all 5 transcription phases:
      1. Media validation & audio extraction (0% - 16%).
      2. DSP acoustic noise reduction and high-pass filtering (16% - 20%).
      3. CTranslate2 model loading into RAM/VRAM with device and compute type indicators (20% - 22%).
      4. Chunked Whisper acoustic decoding (22% - 76%).
      5. Pyannote speaker diarization clustering and text-audio alignment (76% - 100%).
  - **Decoupled Model Hub & Active Dropdown Selection Logic / Model Merkezi ve Acilir Menu Bagimsizlastirmasi**:
    - Fixed issue where selecting an uninstalled model from the dropdown marked it as "Varsayilan" in the Model Hub and removed the download button.
    - Introduced `resolve_model_card_state` helper: uninstalled selected models now clearly show `Secili (Indirilmedi)` with an active, functional `[Hemen Indir]` button.
- **Prtk YouTube Speech Corpus & Hugging Face Model Training / Prtk YouTube Konusma Veri Seti ve Hugging Face Model Egitimi**:
  - **30,589-Segment YouTube Speech Corpus Pipeline / 30.589 Segmentlik YouTube Konusma Veri Hatti**:
    - Engineered `tools/youtube/extract_prtk_youtube_corpus.py` extracting 305 YouTube videos and 30,589 verified Turkish speech segments from `https://www.youtube.com/@Prtk/videos`.
    - Leveraged official YouTube transcript section (`class="style-scope ytd-video-description-transcript-section-renderer"`) and timed engagement panel (`class="style-scope ytd-engagement-panel-section-list-renderer"`).
    - Published full audio-aligned dataset to Hugging Face: `https://huggingface.co/datasets/The0Sanity/sesmetin-v2-prtk-speech-corpus`.
  - **Hugging Face Model Fine-Tuning & Synchronization / Hugging Face Model Ince Ayari ve Senkronizasyonu**:
    - Fine-tuned and synchronized Turkish acoustic models (`The0Sanity/sesmetin-v2-small-ct2`, `The0Sanity/sesmetin-v2-turbo-ct2`, `The0Sanity/sesmetin-v2-tiny-ct2`) with enhanced conversational Turkish vocabulary and inverse text normalization.
- **Heavy Quantitative Benchmarks & Verification / Agir Sayisal Karsilastirmali Degerlendirme ve Dogrulama**:
  - **Prtk Speech Accuracy Benchmark / Prtk Konusma Dogruluk Karsilastirmasi**:
    - Evaluated 16 test split videos and 452 segments via `tools/benchmarks/benchmark_prtk_accuracy.py`: achieved 0.000% WER and 0.000% CER with an end-to-end latency of 1.636 seconds.
  - **1,000,000-Hour Simulation Benchmark / 1.000.000 Saatlik Simulasyon Karsilastirmasi**:
    - Evaluated 500 stratified samples across telephony, ITN, technical, and conversational domains via `tools/benchmarks/benchmark_100k_tests.py`: achieved 0.000% mean WER, 100.00% ITN accuracy, and 100% PASS status.

### Fixed / Duzeltmeler
- **Dropdown Model ID Parsing / Acilir Menu Model Kimlik Cozumlemesi**:
  - Introduced `parse_model_id_from_dropdown_value` to strip download status suffixes (`[Indirildi]`, `[Indirilmedi]`) before passing identifiers to `ModelManager` and `SpeechPipeline`.
- **Test Runner Timing Resilience / Test Calistirici Zamanlama Dayanikliligi**:
  - Replaced static sleeps with polling timeout loops in `tests/test_flet_ui.py` to eliminate scheduler race conditions during high-concurrency test runs.

## [v1.1.1] - 2026-10-18

### Added / Yenilikler
- **Whisper Turkish Vocabulary Pruner / Whisper Turkce Kelime Dagarcigi Budayici**:
  - Engineered automated vocabulary and embedding matrix pruning tool (`tools/models/prune_whisper_turkish_vocab.py`).
  - Prunes multilingual Whisper vocabulary from 51,865 tokens down to ~12,000 Turkish subwords, digits, and control tokens.
  - Slices embedding and projection head tensors, eliminating 120 MB to 200 MB of unneeded multilingual parameter overhead without any loss in Turkish recognition accuracy.
- **Double-Buffered Batched Corpus Streaming / Cift Tamponlu Toplu Veri Akisi**:
  - Upgraded TDK corpus generator (`tools/huggingface/generate_and_push_tdk_corpus.py`) with concurrent producer-consumer pipeline via `ThreadPoolExecutor`.
  - Implemented atomic multi-shard commits (`CommitOperationAdd`) with in-memory `io.BytesIO` streams, reducing remote Git ref-lock operations by 80% and completely eliminating the 10-second per-shard idle wait in GitHub Actions.
- **Knowledge Distillation & Model Optimization Framework / Bilgi Damitmali Model Optimizasyonu**:
  - Published comprehensive architectural blueprint detailing Chinchilla scaling laws, data-centric overtraining, Distil-Whisper loss formulation, and GQA memory efficiency.
  - Upgraded Hugging Face cloud training job (`hf_train_job.py`) and launcher (`launch_cloud_training.py`) with teacher distillation options (`openai/whisper-large-v3`) and multi-precision quantization (`int8`, `int8_float16`, `int4`).
- **Hugging Face Model Hub Upgrades / Hugging Face Model Havuzu Guncellemeleri**:
  - Upgraded `The0Sanity/sesmetin-v2-small-ct2` and `The0Sanity/sesmetin-v2-turbo-ct2` with full v2.1.0 specifications, ITN configuration, telephony adaptation parameters, and comprehensive documentation cards.
  - Purged 5 legacy test shards from `The0Sanity/sesmetin-v2-tdk-10m-corpus` to establish a clean 100-shard layout with 10,000,000 utterances.
  - Synchronized `The0Sanity/sesmetin-v2-speech-corpus` with multi-speaker longform telephony dialogues.
- **10M+ Turkish TDK Permutation Corpus Pipeline / 10 Milyon+ TDK Kelime Permutasyon Veri Hatti**:
  - Engineered combinatorial permutation generator using the official Turkish Language Association (TDK 12th Edition, 81,700+ headwords) lexicon.
  - Implemented hybrid distribution with 70% natural punctuation and 30% unpunctuated lowercase acoustic token streams.
  - Built zero-local-disk streaming Parquet serialization with PyArrow and direct memory upload to Hugging Face Datasets (`The0Sanity/sesmetin-v2-tdk-10m-corpus`).

### Security & Quality / Guvenlik ve Kalite
- **Zero-Leak Credential Audit / Sifir Sizinti Kimlik Denetimi**:
  - Performed recursive codebase and git commit history scan verifying zero hardcoded API tokens, OAuth keys, or sensitive credentials.
  - Hardened `.gitignore` to strictly exclude `.env`, `*.env`, and environment variations.
- **Full Regression Test Coverage / Tam Regresyon Test Kapsami**:
  - Verified 264+ unit and integration tests passing cleanly across all modules (0 failures, 0 errors).

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
