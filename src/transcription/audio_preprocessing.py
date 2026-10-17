"""Acoustic audio preprocessing module for SesMetin Pro.

Provides Voice Activity Detection (VAD) energy gating, pre-emphasis filtering
to accentuate higher-frequency consonant clarity, and peak loudness normalization
prior to speech-to-text inference.
"""

from typing import Optional
import numpy as np


def apply_pre_emphasis(signal: np.ndarray, coefficient: float = 0.97) -> np.ndarray:
    """Apply high-pass pre-emphasis filter to accentuate speech consonants.

    y[t] = x[t] - alpha * x[t-1]

    Args:
        signal: 1D audio waveform array (float32).
        coefficient: Pre-emphasis filtering coefficient (typically 0.95 to 0.97).

    Returns:
        Filtered 1D numpy array with identical length.
    """
    if signal.ndim == 0 or len(signal) == 0:
        return signal

    signal_float = signal.astype(np.float32)
    filtered = np.append(signal_float[0], signal_float[1:] - coefficient * signal_float[:-1])
    return filtered.astype(np.float32)


def normalize_loudness(signal: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Normalize peak signal amplitude to a safe dynamic target level without clipping.

    Args:
        signal: 1D audio waveform array.
        target_peak: Target maximum absolute amplitude (0.0 to 1.0).

    Returns:
        Peak-normalized 1D numpy array (float32).
    """
    if len(signal) == 0:
        return signal

    signal_float = signal.astype(np.float32)
    max_val = float(np.max(np.abs(signal_float)))

    if max_val <= 1e-6:
        return signal_float

    scale = target_peak / max_val
    normalized = signal_float * scale
    return np.clip(normalized, -1.0, 1.0).astype(np.float32)


def voice_activity_filter(
    signal: np.ndarray,
    sample_rate: int = 16000,
    energy_threshold: float = 0.01,
    frame_length_ms: int = 30
) -> np.ndarray:
    """Filter out non-speech silence at the beginning and end of audio.

    Args:
        signal: 1D audio waveform array.
        sample_rate: Audio sampling frequency in Hz (default 16000).
        energy_threshold: Relative RMS energy threshold for active speech.
        frame_length_ms: Duration of each analysis frame in milliseconds.

    Returns:
        Trimmed 1D numpy array containing active speech segments.
    """
    if len(signal) == 0:
        return signal

    frame_size = int(sample_rate * (frame_length_ms / 1000.0))
    if frame_size <= 0 or len(signal) < frame_size:
        return signal

    num_frames = len(signal) // frame_size
    energies = []

    for i in range(num_frames):
        start = i * frame_size
        end = start + frame_size
        frame = signal[start:end]
        rms = float(np.sqrt(np.mean(frame ** 2)))
        energies.append(rms)

    max_energy = max(energies) if energies else 0.0
    if max_energy <= 1e-6:
        return signal

    # Find first and last frame exceeding the energy threshold
    active_indices = [
        i for i, e in enumerate(energies)
        if e >= (energy_threshold * max_energy)
    ]

    if not active_indices:
        return signal

    first_frame = max(0, active_indices[0] - 1)
    last_frame = min(num_frames - 1, active_indices[-1] + 1)

    start_sample = first_frame * frame_size
    end_sample = min(len(signal), (last_frame + 1) * frame_size)

    return signal[start_sample:end_sample].astype(np.float32)


def preprocess_audio_pipeline(
    signal: np.ndarray,
    sample_rate: int = 16000,
    enable_vad: bool = True,
    enable_pre_emphasis: bool = True,
    enable_normalization: bool = True
) -> np.ndarray:
    """End-to-end acoustic preprocessing pipeline.

    Args:
        signal: Raw input audio waveform (1D).
        sample_rate: Audio sampling frequency in Hz.
        enable_vad: Apply Voice Activity Detection silence trimming.
        enable_pre_emphasis: Apply high-frequency boost.
        enable_normalization: Apply peak loudness normalization.

    Returns:
        Cleaned, normalized, and pre-emphasized audio waveform array (float32).
    """
    if len(signal) == 0:
        return signal

    processed = signal.astype(np.float32)

    # 1. Voice activity filtering
    if enable_vad:
        processed = voice_activity_filter(processed, sample_rate=sample_rate)

    # 2. Pre-emphasis filtering
    if enable_pre_emphasis and len(processed) > 1:
        processed = apply_pre_emphasis(processed)

    # 3. Peak normalization
    if enable_normalization:
        processed = normalize_loudness(processed)

    return processed
