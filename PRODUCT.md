# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop

## Users

Turkish-speaking researchers, journalists, content creators, students, and professionals transcribing interviews, meetings, lecture recordings, and video content locally and securely.

## Product Purpose

A minimal, offline desktop application that converts Turkish audio and video into accurate, timestamped, speaker-separated transcripts (X1, X2...) with multi-format export and real-time editing.

## Positioning

Zero-configuration, 100% private, and local-first Turkish transcription and speaker separation optimized for standard consumer hardware (CPU INT8) without cloud subscriptions or data leakage.

## Operating Context

Desktop application on Windows (CustomTkinter) used for processing local media files or YouTube links, reviewing and correcting transcripts, and exporting to subtitles, documents, or data tables.

## Capabilities and Constraints

- Local CPU INT8 Faster-Whisper inference (tiny, base, small, medium, large-v3-turbo).
- Acoustic speaker clustering (local) and optional Pyannote pipeline.
- Audio pre-filtering: 80Hz high-pass filter, noise gate, peak normalization.
- Text post-processing: Turkish punctuation, character normalization, hallucination filtering.
- Multi-format exports: TXT, SRT, VTT, JSON, CSV, Markdown.
- Design constraint: Strictly minimalist UI, zero emojis, high signal-to-noise ratio, clean typography, and low cognitive load.

## Product Principles

- Restraint over decoration: Every interface element must serve a direct functional purpose.
- Zero-friction execution: Automated dependency management with no manual environment configuration required.
- Precision and speed: Rapid in-memory search, find-and-replace, and instant speaker renaming.
- Privacy by design: Complete local processing with no external telemetry or network calls during transcription.
