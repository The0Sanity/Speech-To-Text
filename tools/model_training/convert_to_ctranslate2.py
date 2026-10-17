"""SesMetin Pro - CTranslate2 Model Dönüştürme ve INT8 Kuantizasyon Aracı.

Bu araç, PyTorch/Hugging Face formatındaki Whisper modellerini CTranslate2
çalışma zamanı için optimize eder, INT8 olarak sıkıştırır ve SesMetin Pro
uygulamasında doğrudan çalıştırılabilir hale getirir.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List


def calculate_file_sha256(file_path: Path) -> str:
    """Dosyanın SHA-256 sağlama toplamını hesaplar."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def convert_model_to_ctranslate2(
    model_dir_or_name: str,
    output_dir: str,
    quantization: str = "int8",
    model_version: str = "1.0.0",
    model_id: str = "sesmetin-v1-small",
) -> bool:
    """Whisper modelini CTranslate2 formatına dönüştürür ve meta veri dosyası üretir."""
    try:
        import ctranslate2.converters.transformers as ct_conv
    except ImportError:
        print("HATA: 'ctranslate2' dönüştürücü modülü bulunamadı.")
        print("Lütfen yükleyin: pip install ctranslate2 transformers[torch]")
        return False

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SesMetin Pro CTranslate2 Model Dönüştürme ve Kuantizasyon")
    print(f"Kaynak Model: {model_dir_or_name}")
    print(f"Hedef Dizin: {output_dir}")
    print(f"Kuantizasyon Tipi: {quantization}")
    print("=" * 60)

    try:
        converter = ct_conv.TransformersConverter(
            model_name_or_path=model_dir_or_name,
            copy_files=["tokenizer.json", "preprocessor_config.json"],
        )
        converter.convert(
            output_dir=str(out_path),
            quantization=quantization,
            force=True,
        )
        print("CTranslate2 ağırlık dönüştürmesi tamamlandı.")

        # Meta veri ve sağlama toplamları dosyası oluştur
        file_hashes: Dict[str, str] = {}
        total_size_bytes = 0

        for f in out_path.iterdir():
            if f.is_file():
                size = f.stat().st_size
                total_size_bytes += size
                file_hashes[f.name] = calculate_file_sha256(f)

        metadata = {
            "model_id": model_id,
            "version": model_version,
            "architecture": "Whisper-CTranslate2",
            "quantization": quantization,
            "target_language": "tr",
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "files": file_hashes,
        }

        meta_file = out_path / "model_metadata.json"
        meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Model meta verisi kaydedildi: {meta_file}")
        print(f"Toplam Boyut: {metadata['total_size_mb']} MB")
        return True

    except Exception as e:
        print(f"Dönüştürme sırasında hata oluştu: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SesMetin Pro CTranslate2 Dönüştürücü")
    parser.add_argument("--model", type=str, required=True, help="Dönüştürülecek Hugging Face model yolu veya adı")
    parser.add_argument("--output", type=str, required=True, help="Çıktı CTranslate2 dizini")
    parser.add_argument("--quantization", type=str, default="int8", choices=["int8", "float16", "float32"], help="Kuantizasyon")
    parser.add_argument("--version", type=str, default="1.0.0", help="Model sürüm etiketi")
    parser.add_argument("--model-id", type=str, default="sesmetin-v1-small", help="Model benzersiz kimliği")
    args = parser.parse_args()

    success = convert_model_to_ctranslate2(
        model_dir_or_name=args.model,
        output_dir=args.output,
        quantization=args.quantization,
        model_version=args.version,
        model_id=args.model_id,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
