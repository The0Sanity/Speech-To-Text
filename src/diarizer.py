"""Konuşmacı ayrıştırma (Speaker Diarization) modülü.

İki farklı motor sunar:
1. Akustik Öznitelik Kümeleme (100% Yerel, Token gerektirmez, CPU hızlı)
2. Pyannote Pipeline (Hugging Face Token girildiğinde yüksek kaliteli derin öğrenme modeli)
"""

import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf
from scipy.signal import find_peaks
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


class SpeakerDiarizer:
    """Farklı konuşmacıları ayırt eden ve 'X1', 'X2' etiketlerini üreten sınıf."""

    def __init__(
        self,
        speaker_prefix: str = "X",
        hf_token: Optional[str] = None,
        use_pyannote: bool = False,
    ):
        self.speaker_prefix = speaker_prefix or "X"
        self.hf_token = hf_token
        self.use_pyannote = use_pyannote

    def diarize(
        self,
        audio_path: str,
        speech_segments: Optional[List[Dict[str, Any]]] = None,
        num_speakers: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ses dosyasındaki konuşmacıları ayrıştırır.

        Args:
            audio_path: 16kHz WAV dosya yolu.
            speech_segments: Whisper tarafından tespit edilen konuşma segmentleri.
            num_speakers: Biliniyorsa konuşmacı sayısı (None ise otomatik tespit).
            progress_callback: İlerleme bildirimi fonksiyonu (%75 - %90 arası).

        Returns:
            Konuşmacı aralıkları listesi: [{'speaker': 'X1', 'start': 0.0, 'end': 3.5}, ...]
        """
        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")

        # Eğer Pyannote istenmiş ve token varsa dene
        if self.use_pyannote and self.hf_token:
            try:
                if progress_callback:
                    progress_callback(0.78, "Pyannote derin öğrenme modeliyle konuşmacılar ayrıştırılıyor...")
                return self._diarize_pyannote(audio_path, num_speakers, progress_callback)
            except Exception as e:
                print(f"Pyannote hatası (Yerel akustik motora geçiliyor): {e}")

        if progress_callback:
            progress_callback(0.80, "Yerel akustik motor ile konuşmacı profilleri çıkarılıyor...")

        # Yerel akustik kümeleme motoru
        return self._diarize_acoustic(audio_path, speech_segments, num_speakers, progress_callback)

    def _diarize_acoustic(
        self,
        audio_path: str,
        speech_segments: Optional[List[Dict[str, Any]]],
        num_speakers: Optional[int],
        progress_callback: Optional[Callable[[float, str], None]],
    ) -> List[Dict[str, Any]]:
        """Whisper segmentlerinden akustik öznitelikler çıkararak konuşmacıları kümeler."""
        # Sesi oku
        audio_data, sample_rate = sf.read(audio_path, dtype="float32")
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        total_audio_sec = len(audio_data) / sample_rate

        # Eğer Whisper segmentleri verilmemişse tüm sesi 2.5 saniyelik pencerelere böl
        segments_to_analyze: List[Tuple[float, float]] = []
        if speech_segments:
            for s in speech_segments:
                start = max(0.0, float(s["start"]))
                end = min(total_audio_sec, float(s["end"]))
                if (end - start) >= 0.4:  # En az 400ms konuşma
                    segments_to_analyze.append((start, end))
        else:
            window = 2.5
            hop = 1.25
            t = 0.0
            while t + window <= total_audio_sec:
                segments_to_analyze.append((t, t + window))
                t += hop

        if not segments_to_analyze:
            return [{"speaker": f"{self.speaker_prefix}1", "start": 0.0, "end": total_audio_sec}]

        # Her konuşma parçası için akustik parmak izi vektörü çıkar
        features_list = []
        valid_segments = []

        for start, end in segments_to_analyze:
            start_sample = int(start * sample_rate)
            end_sample = int(end * sample_rate)
            chunk = audio_data[start_sample:end_sample]

            if len(chunk) < int(sample_rate * 0.3):
                continue

            feat = self._extract_audio_features(chunk, sample_rate)
            if feat is not None:
                features_list.append(feat)
                valid_segments.append((start, end))

        if len(features_list) < 2:
            return [{"speaker": f"{self.speaker_prefix}1", "start": 0.0, "end": total_audio_sec}]

        X = np.array(features_list)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Konuşmacı sayısını belirle
        if num_speakers is not None and num_speakers >= 1:
            k = num_speakers
        else:
            k = self._estimate_optimal_k(X_scaled, max_k=min(5, len(valid_segments) - 1))

        if k <= 1:
            if progress_callback:
                progress_callback(0.88, "Tek bir ana konuşmacı tespit edildi. Aralıklar etiketleniyor...")
            return [
                {
                    "speaker": f"{self.speaker_prefix}1",
                    "start": round(start, 2),
                    "end": round(end, 2),
                }
                for start, end in valid_segments
            ]

        if progress_callback:
            progress_callback(0.88, f"{k} farklı konuşmacı tespit edildi. Aralıklar etiketleniyor...")

        # Kümeleme (Agglomerative Clustering - ses grupları için en kararlı yaklaşım)
        clustering = AgglomerativeClustering(n_clusters=k, metric="euclidean", linkage="ward")
        cluster_labels = clustering.fit_predict(X_scaled)

        # Konuşma sürelerine göre en çok konuşan konuşmacıyı X1, sonrakini X2 yap
        cluster_durations: Dict[int, float] = {}
        for idx, label in enumerate(cluster_labels):
            dur = valid_segments[idx][1] - valid_segments[idx][0]
            cluster_durations[label] = cluster_durations.get(label, 0.0) + dur

        sorted_clusters = sorted(cluster_durations.keys(), key=lambda c: cluster_durations[c], reverse=True)
        label_to_speaker = {
            cluster_id: f"{self.speaker_prefix}{rank + 1}"
            for rank, cluster_id in enumerate(sorted_clusters)
        }

        # Sonuç aralıklarını oluştur
        diarized_intervals: List[Dict[str, Any]] = []
        for idx, (start, end) in enumerate(valid_segments):
            spk = label_to_speaker[cluster_labels[idx]]
            diarized_intervals.append({
                "speaker": spk,
                "start": round(start, 2),
                "end": round(end, 2),
            })

        return diarized_intervals

    def _extract_audio_features(self, chunk: np.ndarray, sample_rate: int) -> Optional[np.ndarray]:
        """Bir ses parçası için zengin akustik özellik vektörü (F0, Spektral, Enerji) çıkarır."""
        try:
            # RMS Enerji
            rms = np.sqrt(np.mean(chunk**2) + 1e-12)
            if rms < 1e-4:
                return None  # Sessizlik

            # Sıfır Geçiş Oranı (Zero-Crossing Rate)
            zcr = np.mean(np.abs(np.diff(np.signbit(chunk))))

            # FFT Spektrumu
            n_fft = min(2048, len(chunk))
            windowed = chunk[:n_fft] * np.hanning(n_fft)
            spectrum = np.abs(np.fft.rfft(windowed))
            freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)

            # Spektral Ağırlık Merkezi (Spectral Centroid - sesin kalınlığı/tonu)
            spec_sum = np.sum(spectrum) + 1e-12
            centroid = np.sum(freqs * spectrum) / spec_sum

            # Spektral Düşüş (Spectral Rolloff - enerjinin %85'inin altındaki frekans)
            cum_energy = np.cumsum(spectrum)
            rolloff_idx = np.where(cum_energy >= 0.85 * spec_sum)[0]
            rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else freqs[-1]

            # Mel Filtrebank Enerjileri (16 Mel Bandı)
            mel_energies = self._compute_mel_energies(spectrum, freqs, num_filters=16)

            # Temel Frekans (Pitch / F0 - İnsan ses perdesi 70Hz - 400Hz)
            f0 = self._estimate_f0(chunk, sample_rate)

            # Birleştirilmiş öznitelik vektörü
            features = np.hstack([
                [f0, centroid, rolloff, zcr, np.log(rms + 1e-8)],
                mel_energies,
            ])
            return features
        except Exception:
            return None

    def _estimate_f0(self, chunk: np.ndarray, sample_rate: int) -> float:
        """Otokorelasyon yöntemiyle temel ses perdesini (F0 / Pitch) optimize edilmiş pencere ile hesaplar."""
        min_lag = int(sample_rate / 400)
        max_lag = int(sample_rate / 70)

        if len(chunk) < max_lag * 2:
            return 150.0

        # Hesaplama karmaşıklığını O(N^2) yerine O(N log N) / sabit pencere ile sınırla
        win_size = min(len(chunk), 2048)
        start_idx = (len(chunk) - win_size) // 2
        sig = chunk[start_idx : start_idx + win_size]

        try:
            from scipy.signal import fftconvolve
            corr = fftconvolve(sig, sig[::-1], mode="full")
            corr = corr[len(corr) // 2 :]
        except Exception:
            corr = np.correlate(sig[:max_lag * 2], sig[:max_lag * 2], mode="full")
            corr = corr[len(corr) // 2 :]

        if len(corr) <= max_lag:
            return 150.0

        segment_corr = corr[min_lag:max_lag]
        if len(segment_corr) == 0:
            return 150.0

        peak_idx = np.argmax(segment_corr) + min_lag
        if peak_idx > 0:
            pitch = sample_rate / peak_idx
            return float(pitch)
        return 150.0

    def _compute_mel_energies(self, spectrum: np.ndarray, freqs: np.ndarray, num_filters: int = 16) -> np.ndarray:
        """Basit Mel filtresi enerjilerini hesaplar."""
        min_mel = 2595.0 * np.log10(1.0 + 100.0 / 700.0)
        max_mel = 2595.0 * np.log10(1.0 + min(freqs[-1], 8000.0) / 700.0)
        mel_points = np.linspace(min_mel, max_mel, num_filters + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)

        energies = np.zeros(num_filters)
        for i in range(num_filters):
            low = hz_points[i]
            mid = hz_points[i + 1]
            high = hz_points[i + 2]
            mask = (freqs >= low) & (freqs <= high)
            if np.any(mask):
                band_spec = spectrum[mask]
                energies[i] = np.log(np.sum(band_spec**2) + 1e-6)

        return energies

    def _estimate_optimal_k(self, X: np.ndarray, max_k: int = 5) -> int:
        """Silhouette Skoru ile en tutarlı konuşmacı sayısını belirler (1 veya daha fazla)."""
        if len(X) < 4:
            return 1

        best_k = 1
        best_score = -1.0

        for k in range(2, max_k + 1):
            if k >= len(X):
                break
            try:
                kmeans = KMeans(n_clusters=k, n_init=5, random_state=42)
                labels = kmeans.fit_predict(X)
                score = silhouette_score(X, labels)
                if score > best_score:
                    best_score = score
                    best_k = k
            except Exception:
                continue

        # Belirgin bir küme ayrımı yoksa (Silhouette < 0.22), tek ana konuşmacıdır
        if best_score < 0.22:
            return 1

        return best_k

    def _diarize_pyannote(
        self,
        audio_path: str,
        num_speakers: Optional[int],
        progress_callback: Optional[Callable[[float, str], None]],
    ) -> List[Dict[str, Any]]:
        """Pyannote 3.1 derin öğrenme boru hattını çağırır."""
        from pyannote.audio import Pipeline

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token,
        )

        diarization_params = {}
        if num_speakers:
            diarization_params["num_speakers"] = num_speakers

        diarization = pipeline(audio_path, **diarization_params)

        results = []
        speaker_map: Dict[str, str] = {}
        speaker_count = 0

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker not in speaker_map:
                speaker_count += 1
                speaker_map[speaker] = f"{self.speaker_prefix}{speaker_count}"

            results.append({
                "speaker": speaker_map[speaker],
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
            })

        return results
