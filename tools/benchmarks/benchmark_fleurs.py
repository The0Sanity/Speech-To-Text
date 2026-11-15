"""Measured Turkish accuracy on FLEURS, through the same code path the app uses.

Answers two questions with numbers instead of claims:
  1. Does a SesMetin model beat the stock Whisper model it is based on?
  2. Does each accuracy step (default prompt, HPSS, TDK snapping, audio
     enhancement, the old built-in hotwords) lower or raise the error rate?

Each run is the app's default pipeline with exactly one thing changed.
Results are cached per run in dataset/fleurs_tr/results.json, so the script
can be stopped and restarted.

Usage:
    python tools/benchmarks/benchmark_fleurs.py --samples 150
    python tools/benchmarks/benchmark_fleurs.py --samples 150 --only small-baseline

Official Repository: https://github.com/The0Sanity/Speech-To-Text
"""

import argparse
import csv
import json
import re
import sys
import tarfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "dataset" / "fleurs_tr"
RESULTS_FILE = DATA_DIR / "results.json"

# name -> (model id, the one setting that differs from the app default)
RUNS: Dict[str, Tuple[str, str]] = {
    "tiny-baseline": ("tiny", ""),
    "sesmetin-v2-tiny": ("sesmetin-v2-tiny", ""),
    "small-baseline": ("small", ""),
    "sesmetin-v2-small": ("sesmetin-v2-small", ""),
    "small-no-prompt": ("small", "no_prompt"),
    "small-no-hpss": ("small", "no_hpss"),
    "small-no-tdk-snap": ("small", "no_tdk"),
    "small-no-postprocess": ("small", "no_postprocess"),
    "small-no-enhance": ("small", "no_enhance"),
    "small-old-hotwords": ("small", "old_hotwords"),
}


def turkish_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()


def normalize(text: str) -> List[str]:
    """Lower-case with Turkish casing rules and drop punctuation, as FLEURS references are."""
    joined = re.sub(r"['’]", "", turkish_lower(text))  # "meşhed'deki" is one word
    return re.sub(r"[^\w\s]", " ", joined).split()


def edit_distance(ref: List[str], hyp: List[str]) -> int:
    row = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, row[0] = row[0], i
        for j, h in enumerate(hyp, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (r != h))
    return row[-1]


def load_samples(count: int) -> List[Tuple[Path, str]]:
    """Downloads FLEURS Turkish test data once and returns `count` evenly spread (wav, reference) pairs."""
    from huggingface_hub import hf_hub_download

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tsv = hf_hub_download("google/fleurs", "data/tr_tr/test.tsv", repo_type="dataset", local_dir=DATA_DIR)
    with open(tsv, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE) if len(r) >= 4]
    rows.sort(key=lambda r: r[1])
    step = max(1, len(rows) // count)
    chosen = rows[::step][:count]

    wav_dir = DATA_DIR / "test"
    if not all((wav_dir / r[1]).is_file() for r in chosen):
        archive = hf_hub_download(
            "google/fleurs", "data/tr_tr/audio/test.tar.gz", repo_type="dataset", local_dir=DATA_DIR
        )
        wanted = {r[1] for r in chosen}
        wav_dir.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar:
            for member in tar:
                name = Path(member.name).name
                if member.isfile() and name in wanted:
                    source = tar.extractfile(member)
                    if source is not None:
                        (wav_dir / name).write_bytes(source.read())

    missing = [r[1] for r in chosen if not (wav_dir / r[1]).is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} audio files missing from the archive, e.g. {missing[:3]}")
    # Column 3 is the normalised transcription (lower case, no punctuation).
    return [(wav_dir / r[1], r[3]) for r in chosen]


def prepare_audio(wav: Path, enhance: bool) -> str:
    """The app's steps before recognition: FFmpeg conversion, then optional enhancement. Cached on disk."""
    from src.audio_enhancer import enhance_audio
    from src.audio_processor import extract_audio_to_wav

    prepared_dir = DATA_DIR / "prepared"
    prepared_dir.mkdir(exist_ok=True)
    converted = prepared_dir / f"{wav.stem}.16k.wav"
    if not converted.is_file():
        extract_audio_to_wav(str(wav), str(converted), normalize_loudness=True, apply_bandpass=True)
    if not enhance:
        return str(converted)
    enhanced = prepared_dir / f"{wav.stem}.enh.wav"
    if not enhanced.is_file():
        enhance_audio(str(converted), str(enhanced))
    return str(enhanced)


def run_one(name: str, samples: List[Tuple[Path, str]]) -> Dict[str, object]:
    import src.language_model as language_model
    from src.transcriber import TURKISH_COMMON_DOMAIN_HOTWORDS, WhisperTranscriber

    model_id, change = RUNS[name]
    transcriber = WhisperTranscriber(model_size=model_id, cpu_threads=4)

    original_snap: Optional[Callable] = None
    if change == "no_tdk":
        original_snap = language_model.TDKLanguageModelRescorer.snap_sentence
        language_model.TDKLanguageModelRescorer.snap_sentence = lambda self, sentence: sentence

    errors = words = 0
    audio_seconds = 0.0
    examples = []
    started = time.time()
    try:
        for index, (wav, reference) in enumerate(samples, 1):
            audio = prepare_audio(wav, enhance=change != "no_enhance")
            segments = transcriber.transcribe(
                audio,
                language="tr",
                initial_prompt="" if change == "no_prompt" else None,
                hotwords=" ".join(TURKISH_COMMON_DOMAIN_HOTWORDS) if change == "old_hotwords" else None,
                vocal_isolation=change != "no_hpss",
                apply_postprocessing=change != "no_postprocess",
                # Number formatting is judged by the fixture tests, not by WER: FLEURS spells numbers out.
                apply_itn=False,
                clean_disfluencies=False,
            )
            hypothesis = " ".join(s["text"] for s in segments)
            ref_words, hyp_words = normalize(reference), normalize(hypothesis)
            distance = edit_distance(ref_words, hyp_words)
            errors += distance
            words += len(ref_words)
            if segments:
                audio_seconds += segments[-1]["end"]
            if len(examples) < 5:
                examples.append({"ref": reference, "hyp": hypothesis, "errors": distance})
            if index % 25 == 0:
                print(f"  {name}: {index}/{len(samples)}  WER so far {100 * errors / max(1, words):.2f}%", flush=True)
    finally:
        if original_snap is not None:
            language_model.TDKLanguageModelRescorer.snap_sentence = original_snap

    return {
        "model": model_id,
        "change": change or "none (app default)",
        "samples": len(samples),
        "ref_words": words,
        "word_errors": errors,
        "wer_percent": round(100 * errors / max(1, words), 2),
        "seconds": round(time.time() - started, 1),
        "examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--samples", type=int, default=150)
    parser.add_argument("--only", nargs="*", choices=list(RUNS), help="run only these")
    parser.add_argument("--redo", action="store_true", help="ignore cached results")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    samples = load_samples(args.samples)
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8")) if RESULTS_FILE.is_file() else {}

    for name in args.only or RUNS:
        key = f"{name}@{len(samples)}"
        if key in results and not args.redo:
            continue
        print(f"running {name} on {len(samples)} clips", flush=True)
        try:
            results[key] = run_one(name, samples)
        except Exception as error:  # a missing model repo is a result, not a crash
            results[key] = {"model": RUNS[name][0], "error": f"{type(error).__name__}: {error}"}
        RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'run':28} {'WER %':>7} {'errors':>7} {'words':>7} {'time s':>8}")
    for key, result in results.items():
        if "error" in result:
            print(f"{key:28} FAILED: {result['error'][:90]}")
        else:
            print(
                f"{key:28} {result['wer_percent']:>7} {result['word_errors']:>7} "
                f"{result['ref_words']:>7} {result['seconds']:>8}"
            )


if __name__ == "__main__":
    main()
