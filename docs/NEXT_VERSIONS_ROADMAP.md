# SesMetin Pro - Next Versions Architecture & Roadmap

## 1. Executive Summary & Vision

SesMetin Pro is engineered to be an enterprise-grade, offline-first Turkish speech-to-text, speaker diarization, audio enhancement, and subtitle generation desktop platform. The overarching product vision is **True Zero-Dependency Execution**: an end-user must be able to download a single executable on any stock Windows 10 or Windows 11 machine without Python, Git, C++ build tools, or package managers, and have the application launch, self-provision all necessary engines, and transcribe multimedia immediately.

---

## 2. Root-Cause Analysis of v1.0.0 Executable Limitations

### A. The ModuleNotFoundError: 'unittest' Defect
- **Symptom**: When launching the packaged `SpeechToText.exe`, execution halts with `ModuleNotFoundError: No module named 'unittest'` inside `scipy.signal`.
- **Root Cause**: `scipy.signal` imports `scipy._external.array_api_compat.numpy`, which imports `numpy.testing`, which unconditionally imports Python's standard library `unittest`. In `SpeechToText.spec`, `excludes=['pytest', 'unittest']` had been specified to reduce binary size, unintentionally severing this hidden transitive dependency.
- **Resolution in v1.0.1**: Removed `'unittest'` from `excludes` and explicitly declared `'unittest'`, `'unittest.mock'`, and `'multiprocessing'` in `hiddenimports`.

### B. The RuntimeError: lost sys.stdin Defect
- **Symptom**: Unhandled exceptions triggered a secondary crash: `RuntimeError: lost sys.stdin`.
- **Root Cause**: `main.py` featured a generic `except` block invoking `input("\nPress Enter to exit...")`. In a windowed PyInstaller binary (`console=False`), standard input is detached (`sys.stdin` is `None`). Invoking `input()` in this state raises `RuntimeError`.
- **Resolution in v1.0.1**: Guarded interactive prompts behind `sys.stdin and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()`. In windowed mode, errors are logged to `crash.log` and surfaced to the user via a native Windows modal dialog (`ctypes.windll.user32.MessageBoxW`).

### C. The Ephemeral _MEIPASS Storage Defect
- **Symptom**: Whisper models and user configuration were re-downloaded or reset upon subsequent application launches.
- **Root Cause**: In PyInstaller single-file mode, `Path(__file__)` references an ephemeral directory (`AppData\Local\Temp\_MEIxxxxxx`) created per process and deleted on termination.
- **Resolution in v1.0.1**: Introduced `get_base_dir()` in `src/config.py`. When frozen (`getattr(sys, 'frozen', False)`), the application anchors itself to `Path(sys.executable).parent` (or `%LOCALAPPDATA%\SpeechToText` if the launch directory is read-only).

---

## 3. The Zero-Python Zero-Setup Distribution Architecture

To deliver an application that functions on systems with zero pre-existing development tooling:

```
+-------------------------------------------------------------------------+
|                          End-User Windows Machine                       |
|                          (No Python, No FFmpeg)                         |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  SpeechToText.exe (PyInstaller Single-File)             |
|  - Bundled CPython 3.12 Runtime                                         |
|  - Bundled CTranslate2 & Faster-Whisper                                 |
|  - Bundled Flet / Flutter Desktop Engine                                |
|  - Bundled NumPy, SciPy, Scikit-Learn, soundfile                        |
|  - Built-in Dependency Bootstrapper (src/bootstrapper.py)               |
+-------------------------------------------------------------------------+
                                     |
              +----------------------+----------------------+
              |                                             |
              v                                             v
     [FFmpeg Available?]                           [Model Cached?]
              |                                             |
      +-------+-------+                             +-------+-------+
      |               |                             |               |
     Yes              No                           Yes              No
      |               |                             |               |
   Continue    Show In-App Download              Continue    Prompt Model Selection
               Progress Dialog                               & Cache to Disk
                      |                                             |
              Downloads static FFmpeg                       Downloads from HuggingFace
              to %LOCALAPPDATA%\bin                         to %LOCALAPPDATA%\models
```

### Key Architectural Pillars
1. **Self-Contained Embedded Runtime**: The executable contains the full Python interpreter, standard library, and compiled binary wheels. No local Python installation is required or queried.
2. **Dynamic In-App Dependency Bootstrapper**: Rather than bloating the base download with 150 MB of FFmpeg binaries or forcing users to use the command line, `src/bootstrapper.py` detects missing media tools and provides a one-click automated download of static FFmpeg into `%LOCALAPPDATA%\SpeechToText\bin\`.
3. **Hardware Acceleration Auto-Detection**:
   - Level 1: NVIDIA CUDA 12 + cuDNN (if compatible GPU and drivers are present).
   - Level 2: DirectML / ONNX Runtime acceleration.
   - Level 3: Multi-threaded AVX2/AVX-512 CPU execution (guaranteed fallback on all modern x86_64 machines).

---

## 4. Multi-Version Release Roadmap

### Phase 1: v1.0.4 (Current Release: Asset Integrity, Icon Bundling & HTTP 304 Cache Resolution)
- Bundled Flet Material and Cupertino icon catalog (`icons.json`) with runtime self-healing fallback to prevent missing icon crashes.
- Faster-Whisper Silero VAD ONNX models (`silero_vad_v6.onnx`) and CTranslate2 native assets secured with PyInstaller data hooks.
- GitHub Releases update engine HTTP 304 (Not Modified) cache resolution, accompanied by a bypass flag (`force=True`) for live manual checks.
- Enhanced Windows window elevation and instant display priority on launch.

### Phase 2: v1.1.0 (Model Hub, Cache Management & Hardware Diagnostics)
- **Dual Release Artifacts**:
  1. `SpeechToText-Portable.exe` (~135 MB): Self-bootstrapping standalone executable.
  2. `SpeechToText-Setup.exe` (~280 MB): Inno Setup installer bundling static FFmpeg and the default `small` Turkish acoustic model.
- **Model Cache Manager**: Visual model manager within the Settings tab showing local disk usage, download status, and GPU memory requirements for each model variant (`tiny`, `base`, `small`, `medium`, `large-v3-turbo`).
- **Hardware Acceleration Diagnostics**: Real-time GPU VRAM, CUDA capability, and CPU thread benchmarking panel.

### Phase 3: v1.2.0 (Batch File Processing Queue & Audio DSP Tuning)
- **Multi-File Batch Queue**: Drag-and-drop batch queue processing multiple audio and video files with sequential background transcription.
- **Audio Preprocessing Controls**: Interactive UI sliders for high-pass cutoff frequency, noise gate threshold (dB), and EBU R128 target LUFS normalization.
- **Batch Export Automation**: Single-click export of all queued transcriptions in multiple selected formats simultaneously.
- **Dynamic File Naming Templates**: Customizable output file patterns based on date, time, speaker tags, and model name.

### Phase 4: v1.3.0 (Real-Time Live Speech & Desktop Floating Subtitle Bar)
- **Live Microphone Transcription**: Real-time speech recognition via circular audio buffer streaming into Faster-Whisper.
- **Desktop Floating Subtitle Bar**: Borderless, semi-transparent, always-on-top Flet window designed for live streaming, presentations, and system-wide accessibility.
- **Silero VAD Dynamic Pause Detection**: Dynamic voice activity chunking with 400ms - 600ms pause triggers and boundary padding to prevent mid-sentence cuts.
- **Offline Live Dictation Mode**: Direct streaming of spoken sentences into active desktop applications and system clipboard.

### Phase 5: v1.4.0 (Custom Phonetic Glossary & Advanced Subtitle Export Studio)
- **Custom Phonetic Terminology & Acronym Glossary**: User-defined vocabulary and bias dictionary enhancing recognition accuracy for technical, legal, and medical jargon.
- **Filler Word Filtering Controls**: Configurable toggle to automatically remove or retain speech hesitations and fillers (e.g., "uh", "um", "like", "you know").
- **Subtitle Styling & Preview Studio**: Visual configuration of SRT and VTT subtitles with font size, background opacity, text color, and line wrapping limits.
- **Timestamp Precision Editor**: Interactive waveform-based timeline editor to adjust, split, and merge segment timestamps with millisecond accuracy.

### Phase 6: v2.0.0 (Enterprise Speech Intelligence, Multi-Language & Local LLM Summaries)
- **Cross-Lingual Live Translation**: Automatic transcription in Turkish with concurrent translation into English, German, French, and Spanish.
- **Voice Biometrics & Speaker Profiles**: Speaker profile database allowing users to assign names, avatars, and persistent voice signatures across different recordings.
- **Native Video Hardsubbing Engine**: Built-in FFmpeg subtitle burner that bakes styled SRT/ASS subtitles directly into video files with custom typography and positioning.
- **Zero-Cloud Local LLM Meeting Summary**: Optional integration with local Ollama/Llama.cpp models for zero-cloud meeting summaries, action items, and topic extraction.

---

## 5. Visual Attribution & Licensing Verification

In adherence to the custom MIT License with Prominent Visual Attribution:
- All derivative distributions and user interfaces must maintain the repository badge linking to `https://github.com/The0Sanity/Speech-To-Text`.
- The attribution element must remain in the primary application header and cannot be hidden in nested submenus, obscured, or removed.
