"""Transcription engine wrapper for SesMetin Pro.

Provides unified acoustic preprocessing, Faster-Whisper decoding, and Turkish
phonetic / ITN post-processing into a single cohesive interface.
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np

from src.transcriber import WhisperTranscriber
from src.transcription.audio_preprocessing import preprocess_audio_pipeline
from src.transcription.post_processing import post_process_transcript


class TranscriptionEngine:
    """High-level transcription engine with integrated acoustic and linguistic processing."""

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

        1. Acoustic Preprocessing (VAD energy gating, pre-emphasis, peak normalization)
        2. Acoustic Model Decoding (Faster-Whisper)
        3. Turkish Phonetic & ITN Post-Processing
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
