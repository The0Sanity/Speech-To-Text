"""Empirical Quantitative Accuracy Benchmark on Real Turkish YouTube Audio.

Executes genuine ASR inference on real audio from https://www.youtube.com/watch?v=IrYUYT5C5GI
and measures authentic Word Error Rate (WER) and Character Error Rate (CER)
against canonical user ground truth. No mocking or simulated hypotheses.

Official Repository: https://github.com/The0Sanity/Speech-To-Text
"""

import argparse
import io
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Enforce UTF-8 console output without emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import soundfile as sf
from src.transcriber import WhisperTranscriber
from tools.benchmarks.benchmark_100k_tests import (
    calculate_wer,
    calculate_cer,
    normalize_eval_text,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BenchmarkPrtkAccuracy")

# Ground truth provided by user for the full patates and domates sequence (0-75s) of https://www.youtube.com/watch?v=IrYUYT5C5GI
GROUND_TRUTH_FIRST_75S = (
    "Bir patates patates. 2 patates paates. 3 patates paates. 4 patates paates. "
    "5 patates. 6 patates 7 patates 8 patates 9 patates 10 patates patates patates "
    "patates patates patates bir domates domates 2 domates do dom do domates "
    "3 domates do do domates 4 domates. Do do do domates. 5 domates. 6 domates. "
    "7 domates. 8 domates. 9 domates. 10 domates. Domates domates. Domates domates."
)

DATASET_DIR = ROOT_DIR / "dataset" / "prtk_speech_corpus"
REPORT_PATH = DATASET_DIR / "benchmark_prtk_report.json"
AUDIO_PATH = ROOT_DIR / "temp" / "yt_2d716075.wav"


def run_empirical_audio_benchmark(
    audio_path: Path = AUDIO_PATH,
    duration_seconds: float = 75.0,
    models_to_test: List[str] = None,
) -> Dict[str, Any]:
    """Runs genuine speech-to-text inference on real audio and calculates authentic WER/CER."""
    if models_to_test is None:
        models_to_test = ["small", "sesmetin-v2-tiny"]

    if not audio_path.exists():
        raise FileNotFoundError(f"Real test audio file not found: {audio_path}")

    # Read audio snippet
    audio_data, sr = sf.read(str(audio_path), dtype="float32")
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    max_samples = int(duration_seconds * sr)
    snippet = audio_data[:max_samples]

    snippet_path = ROOT_DIR / "temp" / f"benchmark_{int(duration_seconds)}s.wav"
    snippet_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(snippet_path), snippet, sr)

    ref_clean = normalize_eval_text(GROUND_TRUTH_FIRST_75S)
    logger.info("Evaluating models on real audio: %s (duration: %.1f seconds)", audio_path.name, duration_seconds)
    logger.info("Ground Truth Reference:\n  %s", ref_clean)

    results: Dict[str, Any] = {
        "benchmark_title": "Empirical Quantitative Accuracy Benchmark on Real Turkish Audio",
        "audio_file": audio_path.name,
        "youtube_url": "https://www.youtube.com/watch?v=IrYUYT5C5GI",
        "evaluated_duration_seconds": round(duration_seconds, 1),
        "ground_truth_reference": ref_clean,
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": {},
    }

    print("\n" + "=" * 80)
    print("EMPIRICAL ASR BENCHMARK - REAL AUDIO INFERENCE")
    print(f"Video URL: https://www.youtube.com/watch?v=IrYUYT5C5GI")
    print(f"Sample Duration: {duration_seconds:.1f}s | Audio File: {audio_path.name}")
    print("=" * 80)

    for model_name in models_to_test:
        logger.info("Loading and transcribing with model: %s ...", model_name)
        start_time = time.time()

        try:
            transcriber = WhisperTranscriber(
                model_size=model_name,
                cpu_threads=4,
            )
            segments = transcriber.transcribe(
                str(snippet_path),
                language="tr",
                beam_size=5,
                apply_postprocessing=True,
            )
            elapsed = time.time() - start_time

            raw_text = " ".join(s["text"].strip() for s in segments)
            hyp_clean = normalize_eval_text(raw_text)

            wer = calculate_wer(ref_clean, hyp_clean)
            cer = calculate_cer(ref_clean, hyp_clean)

            wer_pct = round(wer * 100, 2)
            cer_pct = round(cer * 100, 2)

            results["models"][model_name] = {
                "model_name": model_name,
                "segments_count": len(segments),
                "elapsed_seconds": round(elapsed, 2),
                "real_wer_percent": wer_pct,
                "real_cer_percent": cer_pct,
                "hypothesis_text": hyp_clean,
                "status": "PASS" if len(segments) > 0 else "FAIL_EMPTY",
            }

            print(f"\nModel: {model_name}")
            print(f"  Segments: {len(segments)} | Inference Time: {elapsed:.2f}s")
            print(f"  Real WER: {wer_pct:.2f}% | Real CER: {cer_pct:.2f}%")
            print(f"  Hypothesis: {hyp_clean[:120]}...")

        except Exception as e:
            logger.error("Failed to benchmark model %s: %s", model_name, e)
            results["models"][model_name] = {
                "model_name": model_name,
                "error": str(e),
                "status": "ERROR",
            }

    print("\n" + "=" * 80)
    print("SUMMARY OF EMPIRICAL BENCHMARKS")
    print("-" * 80)
    print(f"{'Model':<25} | {'Segments':<10} | {'Time (s)':<10} | {'WER (%)':<10} | {'CER (%)':<10}")
    print("-" * 80)
    for m_name, m_res in results["models"].items():
        if "error" not in m_res:
            print(f"{m_name:<25} | {m_res['segments_count']:<10} | {m_res['elapsed_seconds']:<10.2f} | {m_res['real_wer_percent']:<10.2f} | {m_res['real_cer_percent']:<10.2f}")
        else:
            print(f"{m_name:<25} | ERROR: {m_res['error']}")
    print("=" * 80 + "\n")

    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info("Empirical benchmark report saved to: %s", REPORT_PATH)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run empirical ASR benchmark on real Turkish YouTube audio")
    parser.add_argument("--audio", type=Path, default=AUDIO_PATH, help="Path to WAV audio file")
    parser.add_argument("--duration", type=float, default=75.0, help="Duration in seconds to evaluate")
    parser.add_argument("--models", nargs="+", default=["small", "sesmetin-v2-tiny"], help="Models to benchmark")
    args = parser.parse_args()

    run_empirical_audio_benchmark(
        audio_path=args.audio,
        duration_seconds=args.duration,
        models_to_test=args.models,
    )
