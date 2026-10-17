"""Ses ön-işleme ve iyileştirme modülü.

Whisper'a gönderilmeden önce sesi normalleştirme, gürültü azaltma ve
bant geçiren filtreleme ile iyileştirir. Bu işlemler transkripsiyon
doğruluğunu önemli ölçüde artırır.
"""

import numpy as np
import soundfile as sf
from scipy import signal as scipy_signal
from typing import Optional, Callable


def enhance_audio(
    input_path: str,
    output_path: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> str:
    """Ses dosyasını iyileştirir ve yeni dosyaya kaydeder.
    
    Uygulanan iyileştirmeler:
    1. Yüksek geçiren filtre (80Hz) - Düşük frekans gürültüsünü kaldırır
    2. Gürültü kapısı (Noise Gate) - Sessiz bölümlerdeki gürültüyü bastırır  
    3. Ses normalizasyonu - Ses seviyesini standartlaştırır
    4. Yumuşak sınırlama (Soft Clipping) - Aşırı yüksek sesleri kontrol eder
    """
    if progress_callback:
        progress_callback(0.01, "Ses dosyası iyileştirme için okunuyor...")
    
    audio_data, sample_rate = sf.read(input_path, dtype="float32")
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # 1. Yüksek geçiren filtre (High-pass filter at 80Hz)
    # Removes low-frequency rumble, hum, wind noise
    if progress_callback:
        progress_callback(0.02, "Düşük frekans gürültüsü temizleniyor (80Hz filtre)...")
    audio_data = apply_highpass_filter(audio_data, sample_rate, cutoff_hz=80)
    
    # 2. Gürültü kapısı (Noise Gate)
    # Suppress noise in quiet sections
    if progress_callback:
        progress_callback(0.03, "Gürültü kapısı uygulanıyor...")
    audio_data = apply_noise_gate(audio_data, sample_rate)
    
    # 3. Ses normalizasyonu (Peak normalization to -1dB)
    if progress_callback:
        progress_callback(0.04, "Ses seviyesi normalize ediliyor...")
    audio_data = normalize_audio(audio_data, target_db=-1.0)
    
    # 4. Yumuşak sınırlama
    audio_data = soft_clip(audio_data, threshold=0.95)
    
    # Kaydet
    sf.write(output_path, audio_data, sample_rate, subtype="PCM_16")
    
    if progress_callback:
        progress_callback(0.05, "Ses iyileştirme tamamlandı.")
    
    return output_path


def apply_highpass_filter(audio: np.ndarray, sample_rate: int, cutoff_hz: float = 80.0) -> np.ndarray:
    """Belirtilen frekansın altındaki sesleri keser (DC offset, hum, rumble kaldırır)."""
    nyquist = sample_rate / 2.0
    if cutoff_hz >= nyquist:
        return audio
    normalized_cutoff = cutoff_hz / nyquist
    # 4th order Butterworth high-pass
    sos = scipy_signal.butter(4, normalized_cutoff, btype='high', output='sos')
    return scipy_signal.sosfiltfilt(sos, audio).astype(np.float32)


def apply_noise_gate(audio: np.ndarray, sample_rate: int, 
                     threshold_db: float = -40.0,
                     attack_ms: float = 5.0,
                     release_ms: float = 50.0) -> np.ndarray:
    """Belirli bir eşiğin altındaki sesleri bastırır.
    
    Sessiz bölümlerdeki arka plan gürültüsünü temizler ama
    konuşma bölümlerine dokunmaz.
    """
    threshold_linear = 10 ** (threshold_db / 20.0)
    
    # Calculate short-time RMS energy using a sliding window
    frame_length = int(sample_rate * 0.025)  # 25ms frames
    hop_length = int(sample_rate * 0.010)    # 10ms hop
    
    n_frames = 1 + (len(audio) - frame_length) // hop_length
    if n_frames <= 0:
        return audio
    
    # Compute per-frame RMS
    rms_values = np.zeros(n_frames)
    for i in range(n_frames):
        start = i * hop_length
        frame = audio[start:start + frame_length]
        rms_values[i] = np.sqrt(np.mean(frame ** 2) + 1e-12)
    
    # Create sample-level gain envelope
    gain = np.ones(len(audio), dtype=np.float32)
    for i in range(n_frames):
        start = i * hop_length
        end = min(start + frame_length, len(audio))
        if rms_values[i] < threshold_linear:
            # Apply smooth attenuation (don't hard-zero, reduce by 20dB)
            attenuation = max(0.1, rms_values[i] / (threshold_linear + 1e-12))
            gain[start:end] = np.minimum(gain[start:end], attenuation)
    
    # Smooth the gain envelope to avoid clicks (attack/release)
    attack_samples = max(1, int(sample_rate * attack_ms / 1000))
    release_samples = max(1, int(sample_rate * release_ms / 1000))
    smooth_window = max(attack_samples, release_samples)
    if smooth_window > 1 and smooth_window < len(gain):
        kernel = np.ones(smooth_window) / smooth_window
        gain = np.convolve(gain, kernel, mode='same').astype(np.float32)
    
    return audio * gain


def normalize_audio(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """Peak normalizasyonu ile ses seviyesini standartlaştırır."""
    peak = np.max(np.abs(audio))
    if peak < 1e-8:
        return audio
    target_linear = 10 ** (target_db / 20.0)
    return (audio * (target_linear / peak)).astype(np.float32)


def soft_clip(audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Yumuşak sınırlama - aşırı yüksek değerleri eşiğin ötesinde tanh ile sıkıştırır."""
    result = audio.copy()
    mask = np.abs(audio) > threshold
    if np.any(mask):
        result[mask] = threshold * np.tanh(audio[mask] / threshold)
    return result.astype(np.float32)
