"""Konuşma tanıma, konuşmacı ayrıştırma ve dışa aktarma boru hattı testleri."""

import os
import sys
import unittest
from pathlib import Path

# Proje dizinini ekle
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import soundfile as sf

from src.aligner import (
    align_transcription_and_diarization,
    get_unique_speakers,
    rename_speaker_in_transcript,
)
from src.audio_processor import (
    cleanup_temp_file,
    extract_audio_to_wav,
    format_time,
    get_media_info,
)
from src.diarizer import SpeakerDiarizer
from src.exporter import (
    export_to_csv,
    export_to_json,
    export_to_srt,
    export_to_txt,
)


class TestSpeechPipeline(unittest.TestCase):
    """Boru hattı bileşenlerinin entegrasyon testleri."""

    @classmethod
    def setUpClass(cls):
        """Test için iki farklı tonda konuşmacıyı simüle eden 6 saniyelik sentetik ses üret."""
        cls.test_dir = BASE_DIR / "temp" / "test_run"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.sample_rate = 16000
        duration = 6.0  # saniye

        t = np.linspace(0, duration, int(cls.sample_rate * duration), endpoint=False)
        audio = np.zeros_like(t)

        # Konuşmacı 1 (Erkek tonu: ~130 Hz + harmonikler): 0.5s - 2.5s
        mask_spk1 = (t >= 0.5) & (t <= 2.5)
        t_spk1 = t[mask_spk1]
        audio[mask_spk1] = (
            0.6 * np.sin(2 * np.pi * 130 * t_spk1)
            + 0.3 * np.sin(2 * np.pi * 260 * t_spk1)
            + 0.1 * np.sin(2 * np.pi * 390 * t_spk1)
        )

        # Konuşmacı 2 (Kadın tonu: ~250 Hz + harmonikler): 3.5s - 5.5s
        mask_spk2 = (t >= 3.5) & (t <= 5.5)
        t_spk2 = t[mask_spk2]
        audio[mask_spk2] = (
            0.6 * np.sin(2 * np.pi * 250 * t_spk2)
            + 0.3 * np.sin(2 * np.pi * 500 * t_spk2)
            + 0.1 * np.sin(2 * np.pi * 750 * t_spk2)
        )

        cls.synthetic_wav_path = str(cls.test_dir / "synthetic_dialogue.wav")
        sf.write(cls.synthetic_wav_path, audio.astype(np.float32), cls.sample_rate)

    @classmethod
    def tearDownClass(cls):
        """Test dosyalarını temizle."""
        if Path(cls.synthetic_wav_path).exists():
            cleanup_temp_file(cls.synthetic_wav_path)

    def test_01_media_info_and_format(self):
        """Ses analiz ve zaman formatlama testi."""
        info = get_media_info(self.synthetic_wav_path)
        self.assertAlmostEqual(info["duration_seconds"], 6.0, delta=0.2)
        self.assertEqual(info["channels"], 1)
        self.assertEqual(info["sample_rate"], 16000)

        # format_time
        self.assertEqual(format_time(65), "01:05")
        self.assertEqual(format_time(3665), "01:01:05")

    def test_02_audio_conversion(self):
        """FFmpeg dönüştürme testi."""
        out_wav = extract_audio_to_wav(self.synthetic_wav_path)
        self.assertTrue(os.path.isfile(out_wav))
        cleanup_temp_file(out_wav)

    def test_03_diarization_clustering(self):
        """İki farklı konuşmacının akustik kümelenmesi ve X1, X2 etiketlemesi testi."""
        speech_segments = [
            {"start": 0.5, "end": 2.5, "text": "Konuşmacı bir ses kaydı."},
            {"start": 3.5, "end": 5.5, "text": "Konuşmacı iki ses kaydı."},
        ]

        diarizer = SpeakerDiarizer(speaker_prefix="X")
        diar_result = diarizer.diarize(
            audio_path=self.synthetic_wav_path,
            speech_segments=speech_segments,
            num_speakers=2,
        )

        self.assertGreaterEqual(len(diar_result), 2)
        speakers = {d["speaker"] for d in diar_result}
        self.assertIn("X1", speakers)
        self.assertIn("X2", speakers)

    def test_04_alignment_and_merging(self):
        """Zaman damgaları ve konuşmacı hizalama testi."""
        stt_segments = [
            {"start": 0.5, "end": 1.4, "text": "Merhaba Sayın Başkan."},
            {"start": 1.5, "end": 2.4, "text": "Bugün nasılsınız?"},
            {"start": 3.5, "end": 5.4, "text": "Çok teşekkür ederim, sizleri dinliyorum."},
        ]

        diar_intervals = [
            {"speaker": "X1", "start": 0.4, "end": 2.6},
            {"speaker": "X2", "start": 3.4, "end": 5.6},
        ]

        aligned = align_transcription_and_diarization(stt_segments, diar_intervals, auto_merge_gap=1.5)

        # İlk iki cümle X1 tarafından ardışık söylendiği için tek blokta birleşmeli
        self.assertEqual(len(aligned), 2)
        self.assertEqual(aligned[0]["speaker"], "X1")
        self.assertIn("Merhaba Sayın Başkan. Bugün nasılsınız?", aligned[0]["text"])

        self.assertEqual(aligned[1]["speaker"], "X2")
        self.assertIn("Çok teşekkür ederim", aligned[1]["text"])

    def test_05_rename_speaker(self):
        """Konuşmacı adını topluca değiştirme testi."""
        transcript = [
            {"speaker": "X1", "text": "Cümle 1"},
            {"speaker": "X2", "text": "Cümle 2"},
            {"speaker": "X1", "text": "Cümle 3"},
        ]

        renamed = rename_speaker_in_transcript(transcript, "X1", "Ahmet Bey")
        self.assertEqual(renamed[0]["speaker"], "Ahmet Bey")
        self.assertEqual(renamed[1]["speaker"], "X2")
        self.assertEqual(renamed[2]["speaker"], "Ahmet Bey")

        speakers = get_unique_speakers(renamed)
        self.assertListEqual(speakers, ["Ahmet Bey", "X2"])

    def test_06_exporters(self):
        """TXT, SRT, JSON ve CSV dışa aktarım testleri."""
        transcript = [
            {
                "id": 1,
                "start": 1.0,
                "end": 3.5,
                "start_formatted": "00:01",
                "end_formatted": "00:03",
                "timestamp_display": "[00:01 - 00:03]",
                "speaker": "X1",
                "text": "Bugün toplantı var.",
            },
            {
                "id": 2,
                "start": 4.0,
                "end": 7.0,
                "start_formatted": "00:04",
                "end_formatted": "00:07",
                "timestamp_display": "[00:04 - 00:07]",
                "speaker": "X2",
                "text": "Saat kaçta başlayacak?",
            },
        ]

        txt_p = str(self.test_dir / "test_out.txt")
        srt_p = str(self.test_dir / "test_out.srt")
        json_p = str(self.test_dir / "test_out.json")
        csv_p = str(self.test_dir / "test_out.csv")

        export_to_txt(transcript, txt_p)
        export_to_srt(transcript, srt_p)
        export_to_json(transcript, json_p)
        export_to_csv(transcript, csv_p)

        for p in [txt_p, srt_p, json_p, csv_p]:
            self.assertTrue(os.path.isfile(p), f"Dosya oluşmadı: {p}")
            self.assertGreater(os.path.getsize(p), 0, f"Dosya boş: {p}")


if __name__ == "__main__":
    unittest.main()
