"""SesMetin Pro - Whisper Türkçe LoRA İnce Ayar (Fine-Tuning) Pipeline'ı.

Bu araç, Mozilla Common Voice ve Türkçe konuşma veri setleri üzerinde
Whisper modelini LoRA (Low-Rank Adaptation) tekniğiyle eğitmek ve
SesMetin-v1 özel model ailesini üretmek için kullanılır.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TrainingConfig:
    """Model eğitim hiperparametreleri."""
    base_model_name: str = "openai/whisper-small"
    language: str = "Turkish"
    language_code: str = "tr"
    task: str = "transcribe"
    output_dir: str = "./checkpoints/sesmetin-v1-small"
    num_train_epochs: int = 5
    per_device_train_batch_size: int = 16
    learning_rate: float = 1e-3
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    target_modules: tuple = ("q_proj", "v_proj")


def setup_lora_model(config: TrainingConfig):
    """Whisper temel modelini yükler ve LoRA adaptörlerini enjekte eder."""
    try:
        from peft import LoraConfig, PeftModel, get_peft_model
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
    except ImportError:
        print("HATA: 'transformers' ve 'peft' kütüphaneleri yüklü değil.")
        print("Lütfen yükleyin: pip install transformers peft datasets accelerate soundfile")
        return None, None

    print(f"Temel model yükleniyor: {config.base_model_name}")
    processor = WhisperProcessor.from_pretrained(
        config.base_model_name,
        language=config.language,
        task=config.task,
    )
    model = WhisperForConditionalGeneration.from_pretrained(config.base_model_name)

    # Dondurma ve LoRA yapılandırması
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []

    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=list(config.target_modules),
        lora_dropout=config.lora_dropout,
        bias="none",
    )

    peft_model = get_peft_model(model, lora_config)
    peft_model.print_trainable_parameters()

    return peft_model, processor


def export_and_merge_adapter(peft_model, output_path: str):
    """Eğitilmiş LoRA adaptörlerini ana modelle birleştirerek bağımsız model olarak kaydeder."""
    print(f"LoRA adaptörleri ana modelle birleştiriliyor ve kaydediliyor: {output_path}")
    merged_model = peft_model.merge_and_unload()
    merged_model.save_pretrained(output_path)
    print("Model birleştirme tamamlandı. CTranslate2 dönüştürme aşamasına geçilebilir.")


def main():
    parser = argparse.ArgumentParser(description="SesMetin Pro Türkçe Whisper LoRA Eğitim Aracı")
    parser.add_argument("--base-model", type=str, default="openai/whisper-small", help="Hugging Face model adı")
    parser.add_argument("--output-dir", type=str, default="./models_output/sesmetin-v1-small", help="Çıktı dizini")
    parser.add_argument("--epochs", type=int, default=5, help="Eğitim devir sayısı")
    parser.add_argument("--batch-size", type=int, default=16, help="Toplu işlem boyutu")
    parser.add_argument("--lr", type=float, default=1e-3, help="Öğrenme oranı")
    args = parser.parse_args()

    cfg = TrainingConfig(
        base_model_name=args.base_model,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
    )

    print("=" * 60)
    print("SesMetin Pro Özel Model Eğitim Hazırlığı (LoRA)")
    print(f"Hedef Dil: {cfg.language} ({cfg.language_code})")
    print(f"Temel Mimari: {cfg.base_model_name}")
    print(f"Çıktı Yolu: {cfg.output_dir}")
    print("=" * 60)

    model, processor = setup_lora_model(cfg)
    if model is None:
        sys.exit(1)

    print("Model hazırlığı başarılı. Eğitim veri yükleyicisi bağlandığında eğitim başlatılabilir.")


if __name__ == "__main__":
    main()
