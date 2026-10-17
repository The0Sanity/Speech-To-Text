"""SesMetin Pro - Model Doğruluk ve WER (Word Error Rate) Değerlendirme Aracı.

Bu araç, üretilen modellerin Türkçe test setleri üzerindeki kelime hata oranını (WER)
ve karakter hata oranını (CER) ölçer.
"""

import argparse
import json
import sys
from typing import Dict, List, Tuple


def calculate_wer(reference: str, hypothesis: str) -> float:
    """İki metin arasındaki Kelime Hata Oranını (Word Error Rate) Levenshtein tabanlı hesaplar."""
    ref_words = reference.strip().lower().split()
    hyp_words = hypothesis.strip().lower().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Dinamik programlama matrisi
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    wer = d[len(ref_words)][len(hyp_words)] / float(len(ref_words))
    return round(wer, 4)


def evaluate_dataset(test_samples: List[Dict[str, str]]) -> Dict[str, float]:
    """Test veri seti üzerindeki ortalama WER oranını hesaplar."""
    total_wer = 0.0
    valid_count = 0

    for sample in test_samples:
        ref = sample.get("reference", "")
        hyp = sample.get("hypothesis", "")
        if ref:
            wer = calculate_wer(ref, hyp)
            total_wer += wer
            valid_count += 1

    mean_wer = total_wer / max(1, valid_count)
    return {
        "samples_evaluated": valid_count,
        "mean_wer": round(mean_wer, 4),
        "mean_accuracy_percent": round((1.0 - min(1.0, mean_wer)) * 100, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="SesMetin Pro Türkçe ASR Değerlendirme Aracı")
    parser.add_argument("--eval-file", type=str, help="Referans ve hipotez içeren JSON dosyası")
    args = parser.parse_args()

    # Örnek doğrulama testi
    ref_test = "merhaba sesmetin pro ile ses kaydı başarıyla dönüştürüldü"
    hyp_test = "merhaba sesmetin pro ile ses kaydı basarıyla dönüştürüldü"
    sample_wer = calculate_wer(ref_test, hyp_test)

    print("=" * 60)
    print("SesMetin Pro Türkçe Model Doğruluk Testi")
    print(f"Referans : {ref_test}")
    print(f"Hipotez  : {hyp_test}")
    print(f"Hesaplanan WER: %{sample_wer * 100:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
