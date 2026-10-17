"""Transkript çıktılarının TXT, SRT, VTT, JSON, CSV ve Markdown formatlarında dışa aktarılması modülü."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def to_srt_timestamp(seconds: float) -> str:
    """Saniyeyi SRT formatına dönüştürür (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def to_vtt_timestamp(seconds: float) -> str:
    """Saniyeyi WebVTT formatına dönüştürür (HH:MM:SS.mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


def export_to_txt(
    transcript: List[Dict[str, Any]],
    output_path: str,
    media_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Transkripti okunabilir TXT formatında kaydeder."""
    lines = []
    lines.append("=" * 60)
    lines.append("TÜRKÇE SES TRANSKRİPTİ VE KONUŞMACI RAPORU")
    lines.append("=" * 60)
    if media_info:
        lines.append(f"Kaynak Dosya : {media_info.get('file_name', 'Bilinmiyor')}")
        lines.append(f"Toplam Süre  : {media_info.get('duration_formatted', '00:00')}")
        lines.append(f"Dosya Boyutu : {media_info.get('file_size_mb', 0)} MB")
    lines.append(f"Oluşturulma : {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    lines.append("-" * 60)
    lines.append("")

    for item in transcript:
        spk = item.get("speaker", "X1")
        ts = item.get("timestamp_display", f"[{item.get('start', 0):.1f}s - {item.get('end', 0):.1f}s]")
        text = item.get("text", "")
        lines.append(f"{ts} {spk}: {text}")
        lines.append("")

    content = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def export_to_srt(
    transcript: List[Dict[str, Any]],
    output_path: str,
    include_speaker: bool = True,
) -> str:
    """Transkripti standart video altyazı (.srt) formatında kaydeder."""
    srt_blocks = []
    for idx, item in enumerate(transcript, start=1):
        start_srt = to_srt_timestamp(float(item.get("start", 0.0)))
        end_srt = to_srt_timestamp(float(item.get("end", 0.0)))
        spk = item.get("speaker", "")
        text = item.get("text", "")

        speaker_tag = f"[{spk}] " if include_speaker and spk else ""
        caption = f"{speaker_tag}{text}"

        srt_blocks.append(f"{idx}\n{start_srt} --> {end_srt}\n{caption}\n")

    content = "\n".join(srt_blocks)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def export_to_vtt(
    transcript: List[Dict[str, Any]],
    output_path: str,
    include_speaker: bool = True,
) -> str:
    """Transkripti modern WebVTT (.vtt) formatında kaydeder."""
    vtt_blocks = ["WEBVTT\n"]
    for idx, item in enumerate(transcript, start=1):
        start_vtt = to_vtt_timestamp(float(item.get("start", 0.0)))
        end_vtt = to_vtt_timestamp(float(item.get("end", 0.0)))
        spk = item.get("speaker", "")
        text = item.get("text", "")

        if include_speaker and spk:
            line_text = f"<v {spk}> {text}"
        else:
            line_text = text

        vtt_blocks.append(f"{idx}\n{start_vtt} --> {end_vtt}\n{line_text}\n")

    content = "\n".join(vtt_blocks)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def export_to_markdown(
    transcript: List[Dict[str, Any]],
    output_path: str,
    media_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Transkripti Obsidian/Notion/GitHub uyumlu Markdown (.md) olarak kaydeder."""
    lines = ["# 🎙️ Ses Transkript Raporu\n"]

    if media_info:
        lines.append("| Alan | Değer |")
        lines.append("|---|---|")
        lines.append(f"| **Kaynak Dosya** | `{media_info.get('file_name', 'Bilinmiyor')}` |")
        lines.append(f"| **Toplam Süre** | {media_info.get('duration_formatted', '00:00')} |")
        lines.append(f"| **Dosya Boyutu** | {media_info.get('file_size_mb', 0)} MB |")
        lines.append(f"| **Oluşturulma** | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} |")
        lines.append("\n---\n")

    lines.append("## 📝 Konuşma Akışı\n")
    for item in transcript:
        spk = item.get("speaker", "X1")
        ts = item.get("timestamp_display", f"[{item.get('start', 0):.1f}s - {item.get('end', 0):.1f}s]")
        text = item.get("text", "")
        lines.append(f"> **{ts}** **{spk}**: {text}\n")

    content = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def export_to_json(
    transcript: List[Dict[str, Any]],
    output_path: str,
    media_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Tüm ayrıntıları içeren JSON dosyasını oluşturur."""
    data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "media_info": media_info or {},
            "total_segments": len(transcript),
        },
        "transcript": transcript,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return output_path


def export_to_csv(
    transcript: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """Tablolu analiz için CSV dosyası oluşturur."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["No", "Başlangıç (sn)", "Bitiş (sn)", "Zaman", "Konuşmacı", "Metin"])
        for idx, item in enumerate(transcript, start=1):
            writer.writerow([
                idx,
                item.get("start", 0.0),
                item.get("end", 0.0),
                item.get("timestamp_display", ""),
                item.get("speaker", ""),
                item.get("text", ""),
            ])

    return output_path
