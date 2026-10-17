"""Whisper metin segmentleri ile konuşmacı aralıklarını hizalama ve birleştirme modülü."""

from typing import Any, Dict, List, Optional
from src.audio_processor import format_time


def align_transcription_and_diarization(
    transcription_segments: List[Dict[str, Any]],
    diarization_intervals: List[Dict[str, Any]],
    speaker_prefix: str = "X",
    auto_merge_gap: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Metin parçalarını ilgili konuşmacı etiketleri (X1, X2, vb.) ile eşleştirir
    ve aynı konuşmacının ardışık konuşmalarını birleştirir.

    Args:
        transcription_segments: Whisper'dan dönen [{'start': 0.0, 'end': 2.5, 'text': '...'}]
        diarization_intervals: Diarizer'dan dönen [{'speaker': 'X1', 'start': 0.0, 'end': 3.0}]
        speaker_prefix: Varsayılan konuşmacı ön eki ('X' -> X1, X2)
        auto_merge_gap: Aynı konuşmacının iki cümlesi arasındaki birleştirme eşiği (sn)

    Returns:
        Hizalanmış nihai konuşma kayıtları listesi.
    """
    if not transcription_segments:
        return []

    default_speaker = f"{speaker_prefix}1"
    raw_aligned: List[Dict[str, Any]] = []
    last_known_speaker = default_speaker

    for seg in transcription_segments:
        s_start = float(seg["start"])
        s_end = float(seg["end"])
        text = seg["text"].strip()
        if not text:
            continue

        # En çok çakışan konuşmacıyı tespit et
        speaker_overlaps: Dict[str, float] = {}

        for d_int in diarization_intervals:
            d_start = float(d_int["start"])
            d_end = float(d_int["end"])
            spk = d_int["speaker"]

            # Çakışma süresi
            overlap_start = max(s_start, d_start)
            overlap_end = min(s_end, d_end)
            overlap_dur = max(0.0, overlap_end - overlap_start)

            if overlap_dur > 0:
                speaker_overlaps[spk] = speaker_overlaps.get(spk, 0.0) + overlap_dur

        if speaker_overlaps:
            best_speaker = max(speaker_overlaps.items(), key=lambda item: item[1])[0]
            last_known_speaker = best_speaker
        else:
            best_speaker = last_known_speaker

        raw_aligned.append({
            "speaker": best_speaker,
            "start": s_start,
            "end": s_end,
            "text": text,
            "words": seg.get("words", []),
        })

    # Ardışık aynı konuşmacı bloklarını birleştir (Auto-merge)
    merged_turns: List[Dict[str, Any]] = []

    for item in raw_aligned:
        if not merged_turns:
            merged_turns.append(item.copy())
            continue

        prev = merged_turns[-1]
        gap = item["start"] - prev["end"]

        if prev["speaker"] == item["speaker"] and gap <= auto_merge_gap:
            # Aynı konuşmacı, birleştir
            prev["end"] = item["end"]
            prev["text"] = f"{prev['text']} {item['text']}".strip()
            if "words" in prev and "words" in item:
                prev["words"].extend(item["words"])
        else:
            merged_turns.append(item.copy())

    # Formatlı zaman damgaları ve ID ata
    for idx, turn in enumerate(merged_turns):
        turn["id"] = idx + 1
        turn["start_formatted"] = format_time(turn["start"])
        turn["end_formatted"] = format_time(turn["end"])
        turn["timestamp_display"] = f"[{turn['start_formatted']} - {turn['end_formatted']}]"

    return merged_turns


def rename_speaker_in_transcript(
    transcript: List[Dict[str, Any]],
    old_speaker: str,
    new_name: str,
) -> List[Dict[str, Any]]:
    """Transkriptteki tüm 'old_speaker' etiketlerini 'new_name' ile değiştirir."""
    updated = []
    for item in transcript:
        new_item = item.copy()
        if new_item.get("speaker") == old_speaker:
            new_item["speaker"] = new_name
        updated.append(new_item)
    return updated


def get_unique_speakers(transcript: List[Dict[str, Any]]) -> List[str]:
    """Transkriptte yer alan benzersiz konuşmacıların listesini döndürür."""
    seen = []
    for item in transcript:
        spk = item.get("speaker")
        if spk and spk not in seen:
            seen.append(spk)
    return seen
