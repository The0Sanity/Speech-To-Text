"""Long-form audio chunking and rolling prompt context.

Not called by the app; used by the long-form tests and benchmark tools.
"""

import zlib
from typing import Any, Callable, Dict, List, Optional
import numpy as np



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
