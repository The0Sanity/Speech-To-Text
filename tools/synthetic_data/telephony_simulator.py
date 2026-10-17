"""Telephony audio simulation and dataset preparation tool for SesMetin Pro.

Converts clean speech audio into realistic telephone calls (G.711 / cellular acoustics)
with narrow-band filtering, mu-law quantization, and line noise.
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.transcription.audio_preprocessing import simulate_telephony_audio


def process_audio_file(input_file: Path, output_file: Path, sample_rate: int = 16000) -> Path:
    """Read an audio file, apply telephony degradation, and save output."""
    import soundfile as sf

    data, sr = sf.read(str(input_file), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    phone_audio = simulate_telephony_audio(data, sample_rate=sr)
    os.makedirs(output_file.parent, exist_ok=True)
    sf.write(str(output_file), phone_audio, sr, subtype="PCM_16")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Telephony Audio Simulator")
    parser.add_argument("--input", type=str, required=True, help="Input WAV or MP3 audio file")
    parser.add_argument("--output", type=str, required=True, help="Output telephony audio file")
    args = parser.parse_args()

    in_p = Path(args.input)
    out_p = Path(args.output)
    if not in_p.exists():
        print(f"Error: Input file not found: {in_p}")
        sys.exit(1)

    result = process_audio_file(in_p, out_p)
    print(f"Telephony audio saved to: {result}")


if __name__ == "__main__":
    main()
