# Measured accuracy

Every number here was produced by running the app's own recognition pipeline
on real audio. Nothing is simulated or estimated.

## How it was measured

- **Data:** 150 clips from the FLEURS Turkish test set (Google, public on
  Hugging Face), spread evenly over the set. 2,615 reference words. Short read
  sentences, one speaker per clip.
- **Metric:** word error rate (WER) over the whole set: word errors divided by
  reference words. Lower is better. Text is lower-cased with Turkish casing
  rules and punctuation is removed before comparing.
- **Settings:** CPU, INT8, beam size 5, Turkish. Number formatting and filler
  removal are off, because FLEURS spells numbers out.
- **Machine:** 4 CPU cores, no GPU. Measured 2026-11-15 and 2026-11-16.
- **Reproduce:** `python tools/benchmarks/benchmark_fleurs.py --samples 150`
  (downloads about 465 MB into the git-ignored `dataset/` folder).

## What v1.1.6 delivers

| Model | v1.1.5 | v1.1.6 | Word errors (v1.1.6) |
|---|---|---|---|
| Whisper Tiny | 67.38% | 41.07% | 1,074 of 2,615 |
| Whisper Small | 32.62% | 15.18% | 397 of 2,615 |

The gain comes from removing two steps that were making results worse (see
below). No model changed. Base, Medium, Large-v3 and Large-v3-Turbo have not
been measured.

## What each pipeline step did (Whisper Small, v1.1.5 pipeline)

Each row is the v1.1.5 default pipeline with one setting changed.

| Change | WER | Word errors | Effect |
|---|---|---|---|
| None (v1.1.5 default) | 32.62% | 853 | baseline |
| Lexicon snapping off | 23.71% | 620 | 8.91 points better |
| HPSS vocal filter off | 25.39% | 664 | 7.23 points better |
| Audio enhancement off | 32.39% | 847 | 0.23 points better |
| Text post-processing off | 32.58% | 852 | 0.04 points better |
| Old built-in hotword list on | 32.58% | 852 | 0.04 points better |
| Default Turkish prompt off | 33.19% | 868 | 0.57 points worse |

Decisions taken from this table:

- **Lexicon snapping: removed.** It cost 9 points here with the full 920 KB
  lexicon present. A shipped build does not have that file and falls back to
  an 85-word list, where it rewrote ordinary words ("Ben biz var" became
  "Bes bir ver"), so real users had it worse than this table shows. The
  snapping rows can only be reproduced on the v1.1.5 tag.
- **HPSS vocal filter: off by default.** It still runs in the fallback for
  recordings where voice detection finds almost no speech (music).
- **Audio enhancement, text post-processing, default prompt, hotword list:**
  each moves the result by less than one point, which is inside the noise of a
  150-clip set. None is shown to help.

## The SesMetin models

| Model | File compared with | Result |
|---|---|---|
| `sesmetin-v2-tiny` | `Systran/faster-whisper-tiny` | identical SHA-256, identical 1,762 errors |
| `sesmetin-v2-small` | `Systran/faster-whisper-small` | identical SHA-256, identical 853 errors |
| `sesmetin-v2-turbo` | `mobiuslabsgmbh/faster-whisper-large-v3-turbo` | identical SHA-256 (not run) |
| `sesmetin-v1-tiny`, `-small`, `-turbo` | | repository not found on Hugging Face |

The three v2 model files are copies of the stock Whisper models, and the v1
repositories do not exist, so older versions installed stock Whisper under
those names. v1.1.6 removes all six from the catalog. Old settings that name
them are mapped to the matching stock model, and files already downloaded
under the old names are reused.

## Limits of these numbers

- 150 short read sentences. Not interviews, meetings, phone audio or music.
- One speaker per clip, so nothing here says anything about speaker
  separation.
- FLEURS references contain some digits and foreign names, which count as
  errors for every run alike. Compare rows with each other; do not read a row
  as an absolute accuracy for everyday speech.
- A long-form check on three Turkish YouTube videos with human-made captions
  is planned and not yet done.
