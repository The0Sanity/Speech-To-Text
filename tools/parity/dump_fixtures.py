"""Freezes the behaviour of the pure Python functions as golden fixtures for the Rust port.

Runs every text, alignment and export function over a fixed corpus and writes
the input/output pairs to fixtures/*.json. The Rust tests replay the inputs and
must produce the same outputs. Regenerate only when Python behaviour is changed
on purpose:

    python tools/parity/dump_fixtures.py

The text corpus is every string literal found in the existing tests plus
inputs chosen to cross the Python-to-Rust traps (Turkish casing, slicing of
non-ASCII text, empty values, rounding).

Official Repository: https://github.com/The0Sanity/Speech-To-Text
"""

import ast
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import src.exporter as exporter  # noqa: E402
from src import aligner, itn, text_postprocessor, transcriber  # noqa: E402
from src.transcription import post_processing  # noqa: E402

OUT_DIR = ROOT / "fixtures"

TRAP_TEXTS = [
    "",
    " ",
    "a",
    "I",
    "İ",
    "ı",
    "IŞIK ILIK İSTANBUL İÇİN",
    "Iğdır'dan İzmir'e gittik.",
    "ÇĞİÖŞÜ çğıöşü",
    "yüzde yirmi beş",
    "yüzde yüz",
    "iki bin yirmi altı yılında üç yüz elli lira ödedim",
    "bir milyon iki yüz bin beş yüz kırk üç",
    "sıfır",
    "eksi beş derece",
    "birinci ikinci üçüncü onuncu yüzüncü",
    "on beş dolar yirmi euro elli kuruş",
    "bir bir bir bir bir bir bir bir",
    "evet evet evet evet evet evet evet evet evet evet evet evet",
    "pisi pisi gel buraya yavaş yavaş",
    "ııı şey yani eee bugün hava güzel hani",
    ". . . . . . . .",
    "!!!",
    "Merhaba ,dünya .Nasılsın ?",
    "çok  fazla   boşluk    var",
    "sekiz patates sekiz patates sekiz patates sekiz patates",
    "x" * 300,
    "ğ" * 151,
    "Türkçe karakterli çok uzun bir önceki bölüm metni " * 6,
    "Altyazı M.K.",
    "İzlediğiniz için teşekkür ederim.",
    "5 elma 10 armut 3,5 kilo %20",
    "saat on yedi otuzda buluşalım",
    "doksan dokuz virgül dokuz",
]


def harvest_test_strings() -> List[str]:
    found = set()
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if 2 <= len(text) <= 300 and "\n" not in text and any(c.isalpha() for c in text):
                    found.add(text)
    return sorted(found)


def record(cases: List[Dict[str, Any]], name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    case: Dict[str, Any] = {"fn": name, "args": list(args), "kwargs": kwargs}
    try:
        case["out"] = fn(*json.loads(json.dumps(args)), **kwargs)  # deep copy: some functions mutate
    except Exception as error:  # an exception is behaviour too; the port must fail on the same input
        case["raises"] = type(error).__name__
    cases.append(case)


def text_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    texts = sorted(set(harvest_test_strings()) | set(TRAP_TEXTS))
    for text in texts:
        record(cases, "itn.apply_turkish_itn", itn.apply_turkish_itn, text)
        record(cases, "itn.apply_turkish_itn", itn.apply_turkish_itn, text, remove_fillers=False)
        record(cases, "itn.remove_turkish_disfluencies", itn.remove_turkish_disfluencies, text)
        record(cases, "post_processing.post_process_transcript", post_processing.post_process_transcript, text)
        record(cases, "transcriber.clean_trailing_repetitions", transcriber.clean_trailing_repetitions, text)
        record(cases, "transcriber.is_repetition_loop", transcriber.is_repetition_loop, text)
        record(cases, "transcriber.should_filter_segment", transcriber.should_filter_segment, -0.3, 0.1, text)
        record(cases, "transcriber.build_rolling_prompt", transcriber.build_rolling_prompt, "Bağlam:", text)
        record(cases, "transcriber.build_domain_hotwords", transcriber.build_domain_hotwords, text)
        record(cases, "text_postprocessor._fix_turkish_text", text_postprocessor._fix_turkish_text, text)
        record(cases, "text_postprocessor._is_hallucination", text_postprocessor._is_hallucination, text)
        record(
            cases,
            "text_postprocessor._remove_repeated_phrases",
            text_postprocessor._remove_repeated_phrases,
            text,
        )
    for logprob, no_speech in [(-1.5, 0.7), (-1.0, 0.6), (-0.99, 0.61), (-2.0, 0.5), (0.0, 0.0)]:
        record(
            cases, "transcriber.should_filter_segment", transcriber.should_filter_segment, logprob, no_speech, "merhaba"
        )
    for words in (["yirmi", "beş"], ["bin", "dokuz", "yüz"], ["yüz"], [], ["elma"], ["iki", "milyon", "üç"]):
        record(cases, "itn.words_to_number", itn.words_to_number, words)
    for value in (0, 7, 999, 1000, 1234567, -4500):
        record(cases, "post_processing.format_thousands", post_processing.format_thousands, value)
    return cases


def sample_segments() -> List[List[Dict[str, Any]]]:
    plain = [
        {"id": 1, "start": 0.0, "end": 2.345, "text": "Merhaba, bugün yüzde yirmi beş indirim var."},
        {"id": 2, "start": 2.5, "end": 5.0, "text": "ııı şey evet evet evet evet evet evet evet"},
        {"id": 3, "start": 5.2, "end": 5.3, "text": "."},
        {"id": 4, "start": 6.0, "end": 9.999, "text": "İstanbul'da üç yüz elli lira ödedim."},
        {"id": 5, "start": 10.0, "end": 12.0, "text": "İstanbul'da üç yüz elli lira ödedim."},
        {"id": 6, "start": 12.0, "end": 14.0, "text": "İstanbul'da üç yüz elli lira ödedim."},
        {"id": 7, "start": 3661.5, "end": 3725.004, "text": "Bir saatten uzun kayıt, virgül ve \"tırnak\" içerir."},
    ]
    return [plain, [], [{"id": 1, "start": 0.0, "end": 0.0, "text": ""}], plain[:1]]


def segment_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    intervals = [
        {"speaker": "X1", "start": 0.0, "end": 5.1},
        {"speaker": "X2", "start": 5.1, "end": 11.0},
        {"speaker": "X1", "start": 11.0, "end": 14.0},
    ]
    for segments in sample_segments():
        for flags in ({}, {"apply_itn": False}, {"clean_disfluencies": False}, {"remove_hallucinations": False}):
            record(
                cases,
                "text_postprocessor.postprocess_segments",
                text_postprocessor.postprocess_segments,
                segments,
                **flags,
            )
        for diar in (intervals, [], intervals[:1]):
            for gap in (1.5, 0.0):
                record(
                    cases,
                    "aligner.align_transcription_and_diarization",
                    aligner.align_transcription_and_diarization,
                    segments,
                    diar,
                    auto_merge_gap=gap,
                )
    return cases


def transcript_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    transcripts = [
        aligner.align_transcription_and_diarization(
            sample_segments()[0],
            [{"speaker": "X1", "start": 0.0, "end": 5.1}, {"speaker": "X2", "start": 5.1, "end": 4000.0}],
        ),
        [],
    ]
    media_info = {"file_name": "görüşme.mp3", "duration": 3725.0, "format": "mp3"}

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> "FixedClock":
            return cls(2026, 1, 2, 3, 4, 5)

    exporter.datetime = FixedClock  # the created-at line is the only clock-dependent output

    def export(fn: Callable[..., str], suffix: str) -> Callable[..., str]:
        def run(transcript: List[Dict[str, Any]], **kwargs: Any) -> str:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"out{suffix}"
                fn(transcript, str(path), **kwargs)
                return path.read_bytes().decode("utf-8")

        return run

    for transcript in transcripts:
        record(cases, "exporter.export_to_txt", export(exporter.export_to_txt, ".txt"), transcript)
        record(
            cases, "exporter.export_to_txt", export(exporter.export_to_txt, ".txt"), transcript, media_info=media_info
        )
        record(cases, "exporter.export_to_srt", export(exporter.export_to_srt, ".srt"), transcript)
        record(
            cases, "exporter.export_to_srt", export(exporter.export_to_srt, ".srt"), transcript, include_speaker=False
        )
        record(cases, "exporter.export_to_vtt", export(exporter.export_to_vtt, ".vtt"), transcript)
        record(cases, "exporter.export_to_markdown", export(exporter.export_to_markdown, ".md"), transcript)
        record(
            cases,
            "exporter.export_to_markdown",
            export(exporter.export_to_markdown, ".md"),
            transcript,
            media_info=media_info,
        )
        record(cases, "exporter.export_to_json", export(exporter.export_to_json, ".json"), transcript)
        record(cases, "exporter.export_to_csv", export(exporter.export_to_csv, ".csv"), transcript)
        record(cases, "aligner.get_unique_speakers", aligner.get_unique_speakers, transcript)
        record(cases, "aligner.compute_transcript_statistics", aligner.compute_transcript_statistics, transcript)
        record(cases, "aligner.rename_speaker_in_transcript", aligner.rename_speaker_in_transcript, transcript, "X1", "Ayşe")
        record(cases, "aligner.filter_transcript", aligner.filter_transcript, transcript, "İSTANBUL")
        record(cases, "aligner.filter_transcript", aligner.filter_transcript, transcript, "")
        for case_sensitive in (False, True):
            record(
                cases,
                "aligner.find_and_replace_in_transcript",
                aligner.find_and_replace_in_transcript,
                transcript,
                "istanbul",
                "Ankara",
                case_sensitive=case_sensitive,
            )
    for seconds in (0.0, 0.0005, 59.9996, 3599.9999, 3661.5, 86399.999):
        record(cases, "exporter.to_srt_timestamp", exporter.to_srt_timestamp, seconds)
        record(cases, "exporter.to_vtt_timestamp", exporter.to_vtt_timestamp, seconds)
    return cases


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    groups = {"text": text_cases(), "segments": segment_cases(), "transcript": transcript_cases()}
    for name, cases in groups.items():
        (OUT_DIR / f"{name}.json").write_text(
            json.dumps(cases, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        raised = sum("raises" in c for c in cases)
        print(f"fixtures/{name}.json: {len(cases)} cases ({raised} raise an exception)")


if __name__ == "__main__":
    main()
