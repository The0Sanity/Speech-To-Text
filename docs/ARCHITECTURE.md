# Architecture

How the v1.x Python app is put together, and the shape planned for the Rust
rewrite (ADR 0001).

## The pipeline (v1.x)

One transcription run, driven by `FletSpeechToTextApp` in `src/ui/app.py`:

```
media file or YouTube link
  -> src/youtube_downloader.py     fetch audio with yt-dlp (links only)
  -> src/audio_processor.py        FFmpeg: 16 kHz mono WAV, loudness, band-pass
  -> src/audio_enhancer.py         high-pass, noise gate, normalise (optional)
  -> src/transcriber.py            faster-whisper with voice detection;
                                   repetition and hallucination filters;
                                   retry without voice detection for music
  -> src/text_postprocessor.py     repeated-phrase cleanup, number formatting
       -> src/itn.py               numbers, percent, currency, ordinals
  -> src/diarizer.py               group segments by voice (X1, X2, ...)
  -> src/aligner.py                attach speakers, merge adjacent segments
  -> src/exporter.py               TXT, SRT, VTT, JSON, CSV, Markdown
```

Around the pipeline:

| Module | Job |
|---|---|
| `src/models/catalog.py`, `manager.py` | Which models exist; download, find and delete them |
| `src/hardware.py` | CPU or CUDA, memory checks |
| `src/config.py` | Settings in `%APPDATA%\SesMetinPro\config.json`; app version |
| `src/updater.py` | Check GitHub Releases, download, verify, swap the exe or run the installer |
| `src/bootstrapper.py` | Download FFmpeg on first run |
| `src/ui/` | Flet interface |
| `tools/` | Training, publishing, benchmarks, fixture generation. Not part of the app |

Not used by the app: `src/tts/`, `src/transcription/engine.py`,
`src/language_model.py`, `src/ui_flet/`.

## Planned shape (Rust, v2)

A Cargo workspace in `rust/`:

| Crate | Job |
|---|---|
| `sesmetin-core` | Everything in the pipeline, no interface code |
| `sesmetin-cli` | Command line over the core; used for the parity runs |
| `app` | Tauri 2 shell and the React interface |

The interface and the command line reach the core through one function:

```
pipeline::transcribe(source, options, on_progress, cancel) -> Result<Transcript, Error>
```

Modules behind it, in the order they are ported: `text`, `export`, `align`
(each proven against `fixtures/`), then `audio`, `asr`, `diarize`, `models`,
`youtube`. What must match and what may differ is in `docs/PARITY.md`.
