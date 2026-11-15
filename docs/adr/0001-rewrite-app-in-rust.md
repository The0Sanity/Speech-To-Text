# ADR 0001: Rewrite the desktop app in Rust

- Status: accepted
- Date: 2026-11-15

## Context

SesMetin Pro v1.x is a Python app (Flet interface, faster-whisper, packaged
with PyInstaller and Inno Setup). Two kinds of problem kept recurring:

- **Packaging.** Most fixes between v1.0.0 and v1.1.5 were for the packaged
  exe, not for transcription: missing DLLs, the temporary `_MEIPASS` folder,
  missing icon files, antivirus locks, and an updater that froze, rolled back
  silently or offered the same update forever.
- **Unverified behaviour.** The test suite passed while the pipeline lowered
  accuracy (a lexicon step and a vocal filter together doubled the word error
  rate, see `docs/BENCHMARKS.md`), a module could not run at all, and the
  model list offered stock Whisper under another name.

The second kind was fixed in Python in v1.1.6. The first kind comes from the
toolchain and returns with every dependency upgrade.

## Decision

Rewrite the desktop app in Rust with a Tauri 2 interface (React and
TypeScript). The Python app is replaced and deleted at cut-over; there are no
Python bindings.

- `tools/` (training, Hugging Face publishing, benchmarks) stays in Python.
  It depends on PyTorch and transformers and the app never calls it.
- The Rust core is built first as a command-line program and proven against
  the Python app, then the interface is built on top of it.
- Bug fixes and porting never share a commit. Python behaviour was fixed and
  frozen in v1.1.6; the port copies it. The definition of done is
  `docs/PARITY.md`.
- First Rust release: Windows 10/11, CPU only, Turkish interface, with
  speaker separation, YouTube import and a one-click updater.

## Alternatives considered

- **Keep Python and fix packaging.** Cheapest now. Rejected because the
  packaging problems come from PyInstaller and Flet themselves.
- **Rust core with a Python interface (PyO3).** Keeps the Flet interface and
  therefore the packaging problems.
- **Slint or egui instead of Tauri.** Smaller binaries, but the installer and
  updater would be written by hand again, which is where v1.x failed.

## Consequences

- Models may need one re-download if the Rust speech engine uses a different
  file format. Accepted; the engine is chosen on accuracy and speed.
- The speaker-separation algorithm is replaced, so speaker labels will differ
  from v1.x.
- Until cut-over there are two implementations in the repository. Python gets
  critical fixes only.
- v1.1.6 must be able to hand users over to v2 through its updater.
