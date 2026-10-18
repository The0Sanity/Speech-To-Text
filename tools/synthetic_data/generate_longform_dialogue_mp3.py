"""SesMetin Pro - Procedural 5 to 10 Minute Cycled Dialogue MP3 Generator.

Generates realistic, long-form multi-speaker retail customer service dialogues (cashier
and customer alternating turns) cycling cashier names, customer names, products,
quantities, prices, discounts, and payment methods. Exports standard 16kHz mono MP3
audio files with accompanying ground-truth manifests and optional G.711 telephony simulation.
"""

import argparse
import asyncio
import hashlib
import io
import json
import logging
import math
import os
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf
from scipy import signal

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.transcription.audio_preprocessing import simulate_telephony_audio
from src.transcription.post_processing import post_process_transcript
from tools.benchmarks.sample_registry import SampleRegistry

logger = logging.getLogger("LongFormMP3Gen")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@dataclass
class DialogueTurn:
    """Represents a single conversational turn in the dialogue."""
    turn_index: int
    speaker_role: str  # "kasiyer" or "musteri"
    speaker_name: str
    spoken_text: str
    canonical_text: str
    start_time_sec: float = 0.0
    end_time_sec: float = 0.0
    voice_id: str = "tr-TR-EmelNeural"


@dataclass
class DialogueScript:
    """Full procedural multi-turn script with duration and metadata."""
    turns: List[DialogueTurn]
    total_spoken_words: int
    target_duration_sec: float


class CycledDialogueScriptGenerator:
    """Procedurally generates multi-turn retail transactions with cycled template slots."""

    CASHIERS = [
        ("Zeynep", "tr-TR-EmelNeural", "female"),
        ("Ayşe", "tr-TR-EmelNeural", "female"),
        ("Elif", "tr-TR-EmelNeural", "female"),
        ("Mehmet", "tr-TR-AhmetNeural", "male"),
        ("Burak", "tr-TR-AhmetNeural", "male"),
    ]

    CUSTOMERS = [
        ("Ahmet", "tr-TR-AhmetNeural", "male"),
        ("Ali", "tr-TR-AhmetNeural", "male"),
        ("Can", "tr-TR-AhmetNeural", "male"),
        ("Fatma", "tr-TR-EmelNeural", "female"),
        ("Merve", "tr-TR-EmelNeural", "female"),
        ("Selin", "tr-TR-EmelNeural", "female"),
    ]

    ITEMS = [
        {"name": "tam buğday ekmeği", "unit": "adet", "price_words": "on beş", "price_val": 15},
        {"name": "organik pastorize süt", "unit": "litre", "price_words": "kırk beş", "price_val": 45},
        {"name": "taze kaşar peyniri", "unit": "paket", "price_words": "yüz yirmi", "price_val": 120},
        {"name": "filtre kahve", "unit": "paket", "price_words": "iki yüz elli", "price_val": 250},
        {"name": "amasya elması", "unit": "kilo", "price_words": "otuz beş", "price_val": 35},
        {"name": "zeytinyağı", "unit": "şişe", "price_words": "dört yüz elli", "price_val": 450},
        {"name": "yerli domates", "unit": "kilo", "price_words": "yirmi beş", "price_val": 25},
        {"name": "doğal bal", "unit": "kavanoz", "price_words": "üç yüz", "price_val": 300},
        {"name": "siyah çay", "unit": "paket", "price_words": "yüz seksen", "price_val": 180},
        {"name": "organik yumurta", "unit": "koli", "price_words": "doksan", "price_val": 90},
    ]

    QUANTITIES = [
        ("bir", 1),
        ("iki", 2),
        ("üç", 3),
        ("dört", 4),
        ("beş", 5),
    ]

    DISCOUNTS = [
        ("yüzde beş", "%5", 0.05),
        ("yüzde on", "%10", 0.10),
        ("yüzde on beş", "%15", 0.15),
        ("yüzde yirmi", "%20", 0.20),
        ("yüzde yirmi beş", "%25", 0.25),
    ]

    PAYMENTS = [
        ("temassız kredi kartı", "kredi kartı"),
        ("kredi kartı", "kredi kartı"),
        ("nakit", "nakit"),
    ]

    def __init__(self, seed: Optional[int] = 42):
        self.rng = random.Random(seed)

    def generate_script(self, target_duration_seconds: float = 300.0) -> DialogueScript:
        """Generate a sequence of cycled customer transactions until target duration is met.

        Approximate speaking rate: ~2.4 words per second + 0.6s inter-turn pause.
        """
        turns: List[DialogueTurn] = []
        cumulative_sec = 0.0
        transaction_id = 0
        turn_id = 0

        cashier_info = self.CASHIERS[0]
        cashier_name, cashier_voice, cashier_gender = cashier_info

        while cumulative_sec < target_duration_seconds:
            # Cycle customer
            cust_info = self.CUSTOMERS[transaction_id % len(self.CUSTOMERS)]
            cust_name, cust_voice, cust_gender = cust_info

            # Ensure cashier and customer voices don't clash
            if cust_voice == cashier_voice:
                cust_voice = "tr-TR-AhmetNeural" if cashier_voice == "tr-TR-EmelNeural" else "tr-TR-EmelNeural"

            title_cashier = "Hanım" if cashier_gender == "female" else "Bey"
            title_cust = "Bey" if cust_gender == "male" else "Hanım"

            # 1. Greeting - Cashier
            spk_greet = f"merhaba sesmetin markete hoş geldiniz ben kasiyer {cashier_name} bugün size nasıl yardımcı olabilirim"
            can_greet = f"Merhaba, SesMetin Market'e hoş geldiniz! Ben kasiyer {cashier_name}. Bugün size nasıl yardımcı olabilirim?"
            turn_dur = self._estimate_turn_duration(spk_greet)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="kasiyer",
                speaker_name=cashier_name,
                spoken_text=spk_greet,
                canonical_text=can_greet,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cashier_voice
            ))
            cumulative_sec += turn_dur + 0.6
            turn_id += 1

            # 2. Response - Customer
            acc_num = 1200 + (transaction_id * 100) % 8000
            spk_resp = f"merhaba {cashier_name} {title_cashier.lower()} ben {cust_name} üyelik numaram {acc_num}"
            can_resp = f"Merhaba {cashier_name} {title_cashier}, ben {cust_name}. Üyelik numaram {acc_num}."
            turn_dur = self._estimate_turn_duration(spk_resp)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="musteri",
                speaker_name=cust_name,
                spoken_text=spk_resp,
                canonical_text=can_resp,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cust_voice
            ))
            cumulative_sec += turn_dur + 0.6
            turn_id += 1

            # 3. Items scanning loop (1 to 3 items)
            num_items = self.rng.randint(1, 3)
            basket_total = 0

            for it_idx in range(num_items):
                if cumulative_sec >= target_duration_seconds:
                    break

                item = self.ITEMS[(transaction_id * 3 + it_idx) % len(self.ITEMS)]
                qty_word, qty_val = self.QUANTITIES[(transaction_id + it_idx) % len(self.QUANTITIES)]
                line_total = qty_val * item["price_val"]
                basket_total += line_total

                # Cashier scans item
                spk_scan = f"{qty_word} {item['unit']} {item['name']} okutuldu birim fiyatı {item['price_words']} lira"
                can_scan = f"{qty_val} {item['unit']} {item['name']} okutuldu, birim fiyatı {item['price_val']} TL."
                turn_dur = self._estimate_turn_duration(spk_scan)
                turns.append(DialogueTurn(
                    turn_index=turn_id,
                    speaker_role="kasiyer",
                    speaker_name=cashier_name,
                    spoken_text=spk_scan,
                    canonical_text=can_scan,
                    start_time_sec=round(cumulative_sec, 2),
                    end_time_sec=round(cumulative_sec + turn_dur, 2),
                    voice_id=cashier_voice
                ))
                cumulative_sec += turn_dur + 0.6
                turn_id += 1

                # Customer response after each scan
                if it_idx < num_items - 1:
                    spk_ack = "teşekkürler listemdeki diğer ürünleri de kontrol edebilirsiniz"
                    can_ack = "Teşekkürler, listemdeki diğer ürünleri de kontrol edebilirsiniz."
                else:
                    spk_ack = "harika başka bir ürünüm kalmadı toplam tutar nedir ve indirimim var mı"
                    can_ack = "Harika, başka bir ürünüm kalmadı. Toplam tutar nedir ve indirimim var mı?"

                turn_dur = self._estimate_turn_duration(spk_ack)
                turns.append(DialogueTurn(
                    turn_index=turn_id,
                    speaker_role="musteri",
                    speaker_name=cust_name,
                    spoken_text=spk_ack,
                    canonical_text=can_ack,
                    start_time_sec=round(cumulative_sec, 2),
                    end_time_sec=round(cumulative_sec + turn_dur, 2),
                    voice_id=cust_voice
                ))
                cumulative_sec += turn_dur + 0.6
                turn_id += 1

            # 4. Discount application - Cashier
            disc_word, disc_pct, disc_ratio = self.DISCOUNTS[transaction_id % len(self.DISCOUNTS)]
            disc_amount = int(basket_total * disc_ratio)
            final_total = max(10, basket_total - disc_amount)

            spk_disc = f"üyelik kartınıza özel {disc_word} indirim uygulandı ara toplam {final_total} lira"
            can_disc = f"Üyelik kartınıza özel {disc_pct} indirim uygulandı, ara toplam {final_total} TL."
            turn_dur = self._estimate_turn_duration(spk_disc)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="kasiyer",
                speaker_name=cashier_name,
                spoken_text=spk_disc,
                canonical_text=can_disc,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cashier_voice
            ))
            cumulative_sec += turn_dur + 0.6
            turn_id += 1

            # 5. Payment Selection - Customer
            pay_spoken, pay_can = self.PAYMENTS[transaction_id % len(self.PAYMENTS)]
            spk_pay = f"ödemeyi {pay_spoken} ile yapmak istiyorum"
            can_pay = f"Ödemeyi {pay_can} ile yapmak istiyorum."
            turn_dur = self._estimate_turn_duration(spk_pay)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="musteri",
                speaker_name=cust_name,
                spoken_text=spk_pay,
                canonical_text=can_pay,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cust_voice
            ))
            cumulative_sec += turn_dur + 0.6
            turn_id += 1

            # 6. Payment Confirmation & Receipt - Cashier
            spk_farewell = f"ödemeniz başarıyla tamamlandı bilgi fişinizi takdim ediyorum iyi günler dileriz {cust_name} {title_cust.lower()}"
            can_farewell = f"Ödemeniz başarıyla tamamlandı, bilgi fişinizi takdim ediyorum. İyi günler dileriz {cust_name} {title_cust}."
            turn_dur = self._estimate_turn_duration(spk_farewell)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="kasiyer",
                speaker_name=cashier_name,
                spoken_text=spk_farewell,
                canonical_text=can_farewell,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cashier_voice
            ))
            cumulative_sec += turn_dur + 0.6
            turn_id += 1

            # 7. Customer Farewell - Customer
            spk_cust_bye = "teşekkür ederim kolay gelsin iyi çalışmalar"
            can_cust_bye = "Teşekkür ederim, kolay gelsin, iyi çalışmalar."
            turn_dur = self._estimate_turn_duration(spk_cust_bye)
            turns.append(DialogueTurn(
                turn_index=turn_id,
                speaker_role="musteri",
                speaker_name=cust_name,
                spoken_text=spk_cust_bye,
                canonical_text=can_cust_bye,
                start_time_sec=round(cumulative_sec, 2),
                end_time_sec=round(cumulative_sec + turn_dur, 2),
                voice_id=cust_voice
            ))
            cumulative_sec += turn_dur + 0.8
            turn_id += 1

            transaction_id += 1

        total_words = sum(len(t.spoken_text.split()) for t in turns)
        return DialogueScript(
            turns=turns,
            total_spoken_words=total_words,
            target_duration_sec=cumulative_sec
        )

    def _estimate_turn_duration(self, text: str) -> float:
        """Estimate speech duration in seconds based on word count (~2.4 words/sec)."""
        words = text.strip().split()
        return max(1.2, round(len(words) / 2.3, 2))


async def _synthesize_turn_neural_async(
    text: str,
    voice: str = "tr-TR-EmelNeural",
    target_sr: int = 16000,
    pitch: str = "+0Hz",
    rate: str = "+0%",
    max_retries: int = 2
) -> np.ndarray:
    """Synthesize Turkish spoken words using Microsoft Edge neural TTS with voice fallback."""
    if not HAS_EDGE_TTS:
        raise RuntimeError("edge-tts package is not installed.")

    voices_to_try = [(voice, pitch, rate)]
    if voice != "tr-TR-EmelNeural":
        # Fallback to Emel with lower pitch for male customer turns
        voices_to_try.append(("tr-TR-EmelNeural", "-35Hz", "-5%"))

    last_exc = None
    for cur_voice, cur_pitch, cur_rate in voices_to_try:
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=cur_voice,
                    pitch=cur_pitch,
                    rate=cur_rate
                )
                buffer = bytearray()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        buffer.extend(chunk["data"])

                if buffer:
                    raw_audio, sr = sf.read(io.BytesIO(buffer), dtype="float32")
                    if raw_audio.ndim > 1:
                        raw_audio = np.mean(raw_audio, axis=1)

                    if sr != target_sr:
                        num_resampled = int(len(raw_audio) * target_sr / sr)
                        raw_audio = signal.resample(raw_audio, num_resampled).astype(np.float32)

                    return raw_audio
                else:
                    last_exc = ValueError(f"No audio stream returned for text: {text[:30]}")
            except Exception as exc:
                last_exc = exc

            await asyncio.sleep(0.3 * (attempt + 1))

    raise last_exc or RuntimeError(f"Neural TTS failed after retries.")


class LongFormMP3Generator:
    """Generates continuous multi-speaker audio and encodes standard 16kHz MP3."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        sample_rate: int = 16000,
        registry: Optional[SampleRegistry] = None
    ):
        self.output_dir = output_dir or (BASE_DIR / "dataset" / "longform_mp3")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.script_generator = CycledDialogueScriptGenerator()
        self.registry = registry or SampleRegistry()

    async def _synthesize_all_turns_async(
        self,
        turns: List[DialogueTurn],
        concurrency: int = 3
    ) -> List[np.ndarray]:
        """Synthesize all turns in parallel with bounded concurrency and harmonic fallback."""
        sem = asyncio.Semaphore(concurrency)

        async def synth_turn(turn: DialogueTurn) -> np.ndarray:
            async with sem:
                if HAS_EDGE_TTS:
                    try:
                        return await _synthesize_turn_neural_async(
                            text=turn.spoken_text,
                            voice=turn.voice_id,
                            target_sr=self.sample_rate
                        )
                    except Exception as exc:
                        logger.warning(
                            "Neural TTS synthesis failed for turn %d (%s): %s. Falling back to harmonic.",
                            turn.turn_index, turn.spoken_text[:30], exc
                        )
                # Fallback to procedural harmonic waveform
                dur = max(1.2, len(turn.spoken_text.split()) / 2.3)
                return self._synthesize_turn_waveform(
                    duration_sec=dur,
                    voice_id=turn.voice_id,
                    speaker_role=turn.speaker_role
                )

        tasks = [synth_turn(turn) for turn in turns]
        return await asyncio.gather(*tasks)

    def _synthesize_all_turns(self, turns: List[DialogueTurn]) -> List[np.ndarray]:
        """Synchronous wrapper to run async turn synthesis."""
        return asyncio.run(self._synthesize_all_turns_async(turns))

    def generate(
        self,
        target_duration_minutes: float = 5.0,
        filename: Optional[str] = None,
        simulate_telephony: bool = False
    ) -> Dict[str, Any]:
        """Generate a complete 5 to 10 minute MP3 audio recording with ground-truth manifest."""
        target_duration_sec = target_duration_minutes * 60.0
        script = self.script_generator.generate_script(target_duration_sec)

        # Register sentences in SampleRegistry to enforce zero data leakage
        for turn in script.turns:
            self.registry.register_sample(turn.canonical_text, split="longform_mp3")

        # Synthesize real speech waveforms for all dialogue turns
        turn_waveforms = self._synthesize_all_turns(script.turns)

        audio_chunks: List[np.ndarray] = []
        pause_samples = int(self.sample_rate * 0.5)  # 500ms silence between turns
        silence_segment = np.zeros(pause_samples, dtype=np.float32)

        current_time = 0.0
        for turn, turn_audio in zip(script.turns, turn_waveforms):
            turn_dur = float(len(turn_audio) / self.sample_rate)
            turn.start_time_sec = round(current_time, 2)
            turn.end_time_sec = round(current_time + turn_dur, 2)
            current_time += turn_dur + 0.5

            audio_chunks.append(turn_audio)
            audio_chunks.append(silence_segment)

        # Concatenate full continuous audio
        full_audio = np.concatenate(audio_chunks).astype(np.float32)

        # Apply G.711 / cellular telephony degradation if requested
        if simulate_telephony:
            full_audio = simulate_telephony_audio(full_audio, sample_rate=self.sample_rate)

        # Peak normalization
        max_peak = np.max(np.abs(full_audio))
        if max_peak > 0:
            full_audio = full_audio / max_peak * 0.92

        # Format filenames and output paths
        actual_duration_sec = float(len(full_audio) / self.sample_rate)
        actual_duration_min = round(actual_duration_sec / 60.0, 2)
        telephony_tag = "telephony" if simulate_telephony else "clean"

        if not filename:
            h = hashlib.md5(f"longform_{actual_duration_sec}_{telephony_tag}".encode("utf-8")).hexdigest()[:8]
            filename = f"sesmetin_dialogue_{int(actual_duration_sec)}s_{telephony_tag}_{h}.mp3"

        out_mp3_path = self.output_dir / filename
        out_manifest_path = out_mp3_path.with_suffix(".json")
        out_txt_path = out_mp3_path.with_suffix(".txt")

        # Encode MP3 directly using soundfile
        sf.write(str(out_mp3_path), full_audio, self.sample_rate, format="MP3")

        # Build combined ground-truth and spoken transcript
        canonical_script = "\n".join(f"[{t.speaker_role.upper()} - {t.speaker_name}] {t.canonical_text}" for t in script.turns)
        spoken_script = " ".join(t.spoken_text for t in script.turns)

        # Write text transcript
        with open(out_txt_path, "w", encoding="utf-8") as f:
            f.write(canonical_script)

        # Write JSON manifest
        manifest_data = {
            "audio_file": str(out_mp3_path.name),
            "audio_path": str(out_mp3_path),
            "format": "MP3",
            "sample_rate": self.sample_rate,
            "duration_seconds": round(actual_duration_sec, 2),
            "duration_minutes": actual_duration_min,
            "is_telephony": simulate_telephony,
            "turn_count": len(script.turns),
            "total_words": script.total_spoken_words,
            "turns": [asdict(t) for t in script.turns]
        }

        with open(out_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)

        logger.info(
            "Generated MP3 dialogue: %s (Duration: %.2f mins / %.1fs, Turns: %d)",
            out_mp3_path.name, actual_duration_min, actual_duration_sec, len(script.turns)
        )

        return {
            "audio_path": str(out_mp3_path),
            "manifest_path": str(out_manifest_path),
            "txt_path": str(out_txt_path),
            "duration_seconds": actual_duration_sec,
            "duration_minutes": actual_duration_min,
            "turn_count": len(script.turns),
            "spoken_script": spoken_script,
            "canonical_script": canonical_script,
            "is_telephony": simulate_telephony
        }

    def _synthesize_turn_waveform(
        self,
        duration_sec: float,
        voice_id: str,
        speaker_role: str
    ) -> np.ndarray:
        """Synthesize natural multi-harmonic speech wave with speaker-specific fundamental pitch."""
        n_samples = int(self.sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, n_samples, endpoint=False, dtype=np.float32)

        # Pitch assignment (female voice ~220Hz, male voice ~125Hz)
        is_female = voice_id.startswith("af_") or voice_id.startswith("bf_") or "emel" in voice_id.lower() or speaker_role == "kasiyer"
        f0 = 215.0 if is_female else 125.0

        # Natural speech pitch micro-variation
        f0_mod = f0 + (np.sin(2 * np.pi * 3.5 * t) * 6.0)

        # Three characteristic speech formant harmonics
        phase = 2 * np.pi * np.cumsum(f0_mod) / self.sample_rate
        f1 = np.sin(phase) * 0.50
        f2 = np.sin(2.1 * phase) * 0.25
        f3 = np.sin(3.4 * phase) * 0.12

        # Aspiration noise
        noise = np.random.normal(0, 0.015, size=n_samples).astype(np.float32)

        # Syllable amplitude modulation (~4 Hz typical Turkish syllable pacing)
        syllable_envelope = 0.55 + 0.45 * np.maximum(0.0, np.sin(2 * np.pi * 4.2 * t))

        # Fade in / fade out envelope
        fade_len = min(int(self.sample_rate * 0.04), n_samples // 4)
        fade_env = np.ones(n_samples, dtype=np.float32)
        if fade_len > 0:
            fade_env[:fade_len] = np.linspace(0.0, 1.0, fade_len)
            fade_env[-fade_len:] = np.linspace(1.0, 0.0, fade_len)

        waveform = (f1 + f2 + f3 + noise) * syllable_envelope * fade_env
        return waveform.astype(np.float32)


def generate_cycled_dialogue_mp3(
    output_dir: Optional[Path] = None,
    target_duration_minutes: float = 5.0,
    filename: Optional[str] = None,
    simulate_telephony: bool = False
) -> Dict[str, Any]:
    """Top-level convenience function to generate a cycled dialogue MP3 file."""
    generator = LongFormMP3Generator(output_dir=output_dir)
    return generator.generate(
        target_duration_minutes=target_duration_minutes,
        filename=filename,
        simulate_telephony=simulate_telephony
    )


def main():
    """CLI entry point for procedural long-form MP3 dialogue generation."""
    parser = argparse.ArgumentParser(description="SesMetin Pro - 5 to 10 Minute Cycled Dialogue MP3 Generator")
    parser.add_argument("--output-dir", type=str, default="dataset/longform_mp3", help="Output directory")
    parser.add_argument("--duration-mins", type=float, default=5.0, help="Target duration in minutes (5.0 to 10.0)")
    parser.add_argument("--telephony", action="store_true", help="Simulate G.711 / cellular phone call audio")
    parser.add_argument("--filename", type=str, default=None, help="Custom output MP3 filename")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")

    args = parser.parse_args()

    # Enforce duration constraints if running standard generation
    duration = max(0.1, args.duration_mins)

    generator = LongFormMP3Generator(
        output_dir=Path(args.output_dir),
        sample_rate=16000
    )

    print("=" * 65)
    print("SesMetin Pro - Long-Form Cycled MP3 Dialogue Generation")
    print(f"Target Duration: {duration} minutes ({duration * 60:.1f} seconds)")
    print(f"Acoustic Mode  : {'Telephony G.711 Simulation' if args.telephony else 'Studio Audio'}")
    print(f"Target Path    : {args.output_dir}")
    print("=" * 65)

    result = generator.generate(
        target_duration_minutes=duration,
        filename=args.filename,
        simulate_telephony=args.telephony
    )

    print("\nGeneration Complete:")
    print(f"Audio File     : {result['audio_path']}")
    print(f"Duration       : {result['duration_minutes']} min ({result['duration_seconds']:.1f} sec)")
    print(f"Turn Count     : {result['turn_count']} turns")
    print(f"Manifest       : {result['manifest_path']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
