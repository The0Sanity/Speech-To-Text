"""SesMetin Pro - Kokoro-82M ile Türkçe Sentetik Konuşma Verisi Üretim Aracı.

Bu araç, kesin (ground-truth) metinlerden hareketle çok sesli ve hız varyasyonlu
Türkçe ses örnekleri üretir ve SesMetin-v2 eğitimi için hazır veri seti oluşturur.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.tts.kokoro_engine import KokoroSynthesizer, SyntheticAudioSample

# Eğitim İçin Çok Alanlı ve Fonetik Olarak Zengin Türkçe Cümle Havuzu
TURKISH_TRAINING_CORPUS: List[str] = [
    # 1. Günlük Konuşma ve Doğal İfadeler
    "Merhaba, SesMetin Pro ile ses kayıtlarını yüksek doğrulukla metne dönüştürebilirsiniz.",
    "Bugün hava oldukça güzel, toplantıyı dışarıda yapmayı öneriyorum.",
    "Projenin son teslim tarihi yaklaşırken ekip olarak tüm testleri başarıyla tamamladık.",
    "Görüşme sırasında aldığımız notları hemen çalışma arkadaşlarımla paylaşıyorum.",
    "Yeni sürümde konuşmacı ayrıştırma algoritmaları çok daha kararlı çalışıyor.",

    # 2. Sayılar, Yüzdeler, Tarihler ve Para Birimleri (ITN Testi)
    "Toplam 100.000 test başarıyla uygulandı ve raporlandı.",
    "Modelin kelime hata oranı yüzde sıfır nokta bir seviyesine indirildi.",
    "Toplam maliyet 1500 Türk Lirası olarak belirlendi ve fatura kesildi.",
    "Şirketin üçüncü çeyrek büyüme oranı yüzde 14.8 olarak açıklandı.",
    "Toplantımız 25 Ekim 2026 tarihinde saat 14:30'da başlayacaktır.",
    "Depodaki stok miktarı 450 adetten 120 adede kadar geriledi.",
    "Geliştirici ekibimiz son 24 saat içinde 12 farklı hatayı giderdi.",
    "Ödeme tutarı 45 TL olarak sisteme işlendi.",
    "Toplam bütçe 1.200.000 TL olarak belirlendi.",

    # 3. Teknik, Yazılım ve Yapay Zeka Terimleri
    "Faster-Whisper mimarisi CTranslate2 kütüphanesi üzerinde INT8 kuantizasyon ile çalışır.",
    "SesMetin Pro v2 modeli en düşük kelime hatasına ulaştı.",
    "Ses sinyali 16 kilohertz frekansta ve tek kanallı olarak filtrelendi.",
    "Yapay zeka modellerimiz hem CPU hem de NVIDIA CUDA hızlandırıcılarını desteklemektedir.",
    "Konuşma aktivite tespiti için Silero VAD algoritması hassas kipte devreye alındı.",
    "Akustik önişleme ve son işleme entegre edildi.",
    "Derin öğrenme mimarisi ile akustik model optimize edildi.",

    # 4. Fonetik Zorluklar ve Minimal Çiftler (Hard-Negatives)
    "Hala devam eden çalışmalarımızın yanında hâlâ yeni algoritmalar deniyoruz.",
    "Yüksek kâr marjı hedeflenirken kışın yağan kar işleri aksattı.",
    "Oradaki üç beş kişi haricinde salonda kimse kalmamıştı.",
    "Yapay zeka teknolojisi ses metin pro ile yeni bir seviyeye ulaştı.",
]


def generate_synthetic_dataset(
    output_dir: Path,
    limit: int = 0,
    speed_variants: bool = True,
) -> List[SyntheticAudioSample]:
    """Kokoro-82M sentezleyici ile çok sesli Türkçe eğitim veri seti üretir."""
    synthesizer = KokoroSynthesizer(output_dir=output_dir / "audio")
    voices = ["af_bella", "am_adam", "af_sarah", "am_michael"]
    speeds = [0.85, 1.0, 1.15] if speed_variants else [1.0]

    corpus = TURKISH_TRAINING_CORPUS[:limit] if limit > 0 else TURKISH_TRAINING_CORPUS
    samples: List[SyntheticAudioSample] = []

    print("=" * 60)
    print("SesMetin Pro - Kokoro-82M Sentetik Konuşma Verisi Üretimi")
    print(f"Toplam Kaynak Cümle: {len(corpus)}")
    print(f"Konuşmacı Sesleri: {', '.join(voices)}")
    print(f"Hız Varyasyonları: {speeds}")
    print(f"Hedef Dizin: {output_dir}")
    print("=" * 60)

    count = 0
    total_expected = len(corpus) * (len(speeds) if speed_variants else 1)

    for i, sentence in enumerate(corpus):
        voice = voices[i % len(voices)]
        for spd in speeds:
            sample = synthesizer.synthesize_sample(
                text=sentence,
                voice=voice,
                speed=spd,
                sample_rate=16000,
            )
            samples.append(sample)
            count += 1
            if count % 5 == 0 or count == total_expected:
                print(f"[{count}/{total_expected}] Üretildi: {sample.voice} ({spd}x) - '{sentence[:30]}...' ({sample.duration_seconds}s)")

    # Manifest JSONL kaydet
    manifest_path = output_dir / "metadata.jsonl"
    synthesizer.save_dataset_manifest(samples, manifest_path)

    total_duration = sum(s.duration_seconds for s in samples)
    print("=" * 60)
    print("Sentetik Veri Üretimi Başarıyla Tamamlandı!")
    print(f"Toplam Örnek Sayısı : {len(samples)}")
    print(f"Toplam Ses Süresi   : {total_duration:.2f} saniye")
    print(f"Manifest Dosyası    : {manifest_path}")
    print("=" * 60)

    return samples


def main():
    parser = argparse.ArgumentParser(description="Kokoro-82M ile Türkçe Sentetik Veri Üretimi")
    parser.add_argument("--output-dir", type=str, default="./dataset/synthetic_speech", help="Çıktı dizini")
    parser.add_argument("--limit", type=int, default=0, help="Üretilecek cümle sınırı (0: tümü)")
    parser.add_argument("--no-speed-variants", action="store_true", help="Sadece 1.0x hızda üret")
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    generate_synthetic_dataset(
        output_dir=out_path,
        limit=args.limit,
        speed_variants=not args.no_speed_variants,
    )


if __name__ == "__main__":
    main()
