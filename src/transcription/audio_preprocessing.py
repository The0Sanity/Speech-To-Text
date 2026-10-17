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


def simulate_telephony_audio(
    signal: np.ndarray,
    sample_rate: int = 16000,
    add_noise: bool = True,
    apply_mulaw: bool = True
) -> np.ndarray:
    """Simulate telephone network acoustics (G.711 / cellular narrow-band channel).

    Applies:
    1. 300 Hz - 3400 Hz 4th order bandpass filter.
    2. 8-bit ITU-T G.711 mu-law quantization distortion.
    3. Low-level line noise (PSTN / cellular line hiss).

    Args:
        signal: Input 1D audio waveform.
        sample_rate: Audio sampling frequency in Hz (typically 16000).
        add_noise: Whether to inject line hiss.
        apply_mulaw: Whether to apply mu-law 8-bit companding.

    Returns:
        Degraded telephone audio waveform (float32).
    """
    if len(signal) == 0:
        return signal

    import scipy.signal

    sig = signal.astype(np.float32)

    # 1. 300 Hz - 3400 Hz bandpass filter
    nyq = sample_rate * 0.5
    low_norm = max(0.01, 300.0 / nyq)
    high_norm = min(0.99, 3400.0 / nyq)

    sos = scipy.signal.butter(4, [low_norm, high_norm], btype="bandpass", output="sos")
    bandpassed = scipy.signal.sosfilt(sos, sig).astype(np.float32)

    # 2. 8-bit mu-law companding
    if apply_mulaw and np.max(np.abs(bandpassed)) > 1e-6:
        max_val = float(np.max(np.abs(bandpassed)))
        norm_sig = np.clip(bandpassed / max_val, -1.0, 1.0)
        mu = 255.0
        # Compression
        companded = np.sign(norm_sig) * (np.log(1.0 + mu * np.abs(norm_sig)) / np.log(1.0 + mu))
        # 8-bit quantization (256 discrete levels)
        quantized = np.round((companded + 1.0) * 127.5) / 127.5 - 1.0
        # Expansion
        decompanded = np.sign(quantized) * (1.0 / mu) * ((1.0 + mu) ** np.abs(quantized) - 1.0)
        bandpassed = (decompanded * max_val).astype(np.float32)

    # 3. Line noise injection
    if add_noise:
        rms = float(np.sqrt(np.mean(bandpassed ** 2)))
        noise_level = max(1e-4, rms * 0.02)
        noise = np.random.normal(0, noise_level, len(bandpassed)).astype(np.float32)
        bandpassed = bandpassed + noise

    return normalize_loudness(bandpassed, target_peak=0.95)


def detect_telephony_audio(signal: np.ndarray, sample_rate: int = 16000) -> bool:
    """Detect whether an audio signal exhibits narrow-band telephone acoustic profile.

    Checks energy distribution: Telephone audio has steep rolloff above 3400 Hz.
    """
    if len(signal) < 1600:
        return False

    import scipy.signal

    nyq = sample_rate * 0.5
    # High-frequency band: 4000 Hz - 7500 Hz
    if nyq <= 4200:
        return False

    high_cutoff = min(0.95, 4000.0 / nyq)
    sos_high = scipy.signal.butter(2, high_cutoff, btype="highpass", output="sos")
    high_energy = float(np.mean(scipy.signal.sosfilt(sos_high, signal) ** 2))

    # Passband: 300 Hz - 3400 Hz
    sos_pass = scipy.signal.butter(2, [300.0 / nyq, 3400.0 / nyq], btype="bandpass", output="sos")
    pass_energy = float(np.mean(scipy.signal.sosfilt(sos_pass, signal) ** 2))

    if pass_energy <= 1e-7:
        return False

    # Telephone audio has less than 2.5% high-frequency energy compared to speech passband
    ratio = high_energy / pass_energy
    return ratio < 0.025


def adaptive_telephony_equalizer(signal: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """Enhance intelligibility of telephone audio by restoring high-frequency presence.

    Applies resonant peaking filter in the upper speech intelligibility band (2800 Hz - 3400 Hz)
    and loudness normalization.
    """
    if len(signal) == 0:
        return signal

    import scipy.signal

    sig = signal.astype(np.float32)
    nyq = sample_rate * 0.5

    # Peaking bandpass around 3000 Hz to boost consonant plosives and fricatives
    center_freq = min(3000.0, nyq * 0.8)
    q = 2.0
    bw = center_freq / q
    low = max(0.01, (center_freq - bw * 0.5) / nyq)
    high = min(0.99, (center_freq + bw * 0.5) / nyq)

    sos_boost = scipy.signal.butter(2, [low, high], btype="bandpass", output="sos")
    boosted_band = scipy.signal.sosfilt(sos_boost, sig)

    # Mix original with consonant boost
    enhanced = sig + (0.35 * boosted_band)
    return normalize_loudness(enhanced, target_peak=0.95)


def preprocess_audio_pipeline(
    signal: np.ndarray,
    sample_rate: int = 16000,
    enable_vad: bool = True,
    enable_pre_emphasis: bool = True,
    enable_normalization: bool = True,
    enable_telephony_equalizer: bool = True
) -> np.ndarray:
    """End-to-end acoustic preprocessing pipeline.

    Args:
        signal: Raw input audio waveform (1D).
        sample_rate: Audio sampling frequency in Hz.
        enable_vad: Apply Voice Activity Detection silence trimming.
        enable_pre_emphasis: Apply high-frequency boost.
        enable_normalization: Apply peak loudness normalization.
        enable_telephony_equalizer: Auto-detect and equalize telephone audio.

    Returns:
        Cleaned, normalized, and pre-emphasized audio waveform array (float32).
    """
    if len(signal) == 0:
        return signal

    processed = signal.astype(np.float32)

    # 1. Voice activity filtering
    if enable_vad:
        processed = voice_activity_filter(processed, sample_rate=sample_rate)

    # 2. Adaptive telephony equalizer (auto-detects phone calls)
    if enable_telephony_equalizer and detect_telephony_audio(processed, sample_rate=sample_rate):
        processed = adaptive_telephony_equalizer(processed, sample_rate=sample_rate)

    # 3. Pre-emphasis filtering
    if enable_pre_emphasis and len(processed) > 1:
        processed = apply_pre_emphasis(processed)

    # 4. Peak normalization
    if enable_normalization:
        processed = normalize_loudness(processed)

    return processed
