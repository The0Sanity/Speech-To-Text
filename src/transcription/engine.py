"""Transcription engine wrapper for SesMetin Pro.

Provides unified acoustic preprocessing, long-form semantic VAD chunking,
rolling prompt context cache, and Turkish phonetic / ITN post-processing
into a single cohesive interface.
"""

import re
import zlib
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from src.transcriber import WhisperTranscriber
from src.transcription.audio_preprocessing import preprocess_audio_pipeline
from src.transcription.post_processing import post_process_transcript


class LongFormAudioProcessor:
    """Manages semantic chunking and rolling context prompts for long-form (5-10 minute) audio."""

    def __init__(self, chunk_target_sec: float = 30.0, max_context_chars: int = 120):
        self.chunk_target_sec = chunk_target_sec
        self.max_context_chars = max_context_chars

    def split_longform_audio(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        search_window_sec: float = 6.0
    ) -> List[Dict[str, Any]]:
        """Split long audio into semantic chunks at natural pause boundaries without clipping speech."""
        if len(audio) == 0:
            return []

        total_samples = len(audio)
        total_duration = total_samples / sample_rate

        if total_duration <= self.chunk_target_sec * 1.2:
            return [{
                "id": 0,
                "audio": audio,
                "start_sec": 0.0,
                "end_sec": round(total_duration, 2),
                "duration_sec": round(total_duration, 2)
            }]

        chunks = []
        start_idx = 0
        chunk_id = 0
        target_step = int(self.chunk_target_sec * sample_rate)
        window_step = int(search_window_sec * sample_rate)

        while start_idx < total_samples:
            ideal_end = start_idx + target_step
            if ideal_end >= total_samples:
                end_idx = total_samples
            else:
                # Search for lowest energy frame in window around ideal_end
                search_start = max(start_idx + int(10.0 * sample_rate), ideal_end - window_step // 2)
                search_end = min(total_samples, ideal_end + window_step // 2)

                frame_size = int(0.05 * sample_rate)  # 50ms frames
                best_split = ideal_end
                min_energy = float("inf")

                for f_start in range(search_start, search_end - frame_size, frame_size):
                    frame = audio[f_start:f_start + frame_size]
                    energy = float(np.mean(frame ** 2))
                    if energy < min_energy:
                        min_energy = energy
                        best_split = f_start + frame_size // 2

                end_idx = best_split

            chunk_audio = audio[start_idx:end_idx]
            s_sec = round(start_idx / sample_rate, 2)
            e_sec = round(end_idx / sample_rate, 2)

            chunks.append({
                "id": chunk_id,
                "audio": chunk_audio,
                "start_sec": s_sec,
                "end_sec": e_sec,
                "duration_sec": round(e_sec - s_sec, 2)
            })

            chunk_id += 1
            start_idx = end_idx

        return chunks

    def build_rolling_prompt(self, segments: List[Dict[str, Any]]) -> str:
        """Construct bounded prompt context from recent segments, filtering repetition loops."""
        if not segments:
            return ""

        recent_texts = []
        for s in reversed(segments):
            txt = s.get("text", "").strip()
            if not txt:
                continue

            # Check for repetition loops
            words = txt.split()
            if len(words) >= 4 and len(set(w.lower() for w in words)) == 1:
                continue

            # Compression check to reject hallucination loops
            raw_bytes = txt.encode("utf-8")
            if len(raw_bytes) > 20:
                comp_ratio = len(raw_bytes) / max(1, len(zlib.compress(raw_bytes)))
                if comp_ratio > 2.4:
                    continue

            recent_texts.insert(0, txt)
            combined = " ".join(recent_texts)
            if len(combined) >= self.max_context_chars:
                break

        full_prompt = " ".join(recent_texts).strip()
        if len(full_prompt) > self.max_context_chars:
            full_prompt = full_prompt[-self.max_context_chars:].strip()
            space_idx = full_prompt.find(" ")
            if space_idx != -1:
                full_prompt = full_prompt[space_idx + 1:].strip()

        return full_prompt


class TranscriptionEngine:
    """High-level transcription engine with integrated acoustic, long-form, and linguistic processing."""

    def __init__(
        self,
        model_size_or_path: str = "sesmetin-v2-turbo",
        device: str = "auto",
        compute_type: str = "auto"
    ):
        self.transcriber = WhisperTranscriber(
            model_size_or_path=model_size_or_path,
            device=device,
            compute_type=compute_type
        )
        self.longform_processor = LongFormAudioProcessor()

    def transcribe(
        self,
        audio_data: Any,
        language: str = "tr",
        beam_size: int = 5,
        enable_acoustic_preprocessing: bool = True,
        enable_turkish_post_processing: bool = True,
        progress_callback: Optional[Callable[[float, str, Optional[Dict[str, Any]]], None]] = None,
        cancel_event: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute full transcription pipeline.

        1. Acoustic Preprocessing (VAD, telephony equalization, peak normalization)
        2. Semantic Long-Form Chunking with Rolling Context Prompting (if >45s)
        3. Faster-Whisper Model Decoding
        4. Turkish Phonetic & ITN Post-Processing
        """
        # Step 1: Preprocessing
        if enable_acoustic_preprocessing and isinstance(audio_data, np.ndarray):
            audio_data = preprocess_audio_pipeline(audio_data, sample_rate=16000)

        # Step 2: Decoding
        segments = self.transcriber.transcribe(
            audio_data=audio_data,
            language=language,
            beam_size=beam_size,
            apply_postprocessing=True,
            progress_callback=progress_callback,
            cancel_event=cancel_event
        )

        # Step 3: Turkish Phonetic & ITN Post-Processing
        if enable_turkish_post_processing:
            for seg in segments:
                seg["text"] = post_process_transcript(seg["text"])

        return segments
