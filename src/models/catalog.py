"""SesMetin Pro model kataloğu ve model özellikleri tanımları."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ModelCategory(str, Enum):
    """Model kategorisi (SesMetin Özel veya Resmi Whisper)."""
    SESMETIN = "sesmetin"
    WHISPER = "whisper"


@dataclass
class ModelSpecification:
    """ASR modeli teknik özellikleri ve meta verisi."""
    model_id: str
    name: str
    category: ModelCategory
    version: str
    size_mb: int
    ram_req_gb: float
    wer_turkish: str
    description: str
    is_proprietary: bool = False
    ct2_quantization: str = "int8"
    repo_id: str = ""
    fallback_repo_id: str = ""
    files: List[str] = field(default_factory=lambda: ["model.bin", "config.json", "vocabulary.json"])
    system_prompt: str = ""


# SesMetin Pro Resmi ve Özel Model Kataloğu
MODEL_CATALOG: Dict[str, ModelSpecification] = {
    # ------------------ SesMetin-v2 Sentetik Sesle Güçlendirilmiş Modeller ------------------
    "sesmetin-v2-turbo": ModelSpecification(
        model_id="sesmetin-v2-turbo",
        name="SesMetin-v2 Turbo (Özel Türkçe v2 Turbo)",
        category=ModelCategory.SESMETIN,
        version="2.1.0",
        size_mb=1550,
        ram_req_gb=3.5,
        wer_turkish="%4.2 WER",
        description="Kokoro-82M çok konuşmacılı sentetik veri, akustik önişleme ve Türkçe ITN/fonetik düzeltme motoruyla güçlendirilmiş amiral gemisi model.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v2-turbo-ct2",
        fallback_repo_id="Systran/faster-whisper-large-v3-turbo",
        system_prompt="Bu kayıt Türkçe konuşma içermektedir. Kokoro-82M sentetik veri seti ve ITN motoruyla optimize edilmiş v2.1 mimarisi.",
    ),
    "sesmetin-v2-small": ModelSpecification(
        model_id="sesmetin-v2-small",
        name="SesMetin-v2 Small (Özel Türkçe v2 Dengeli)",
        category=ModelCategory.SESMETIN,
        version="2.1.0",
        size_mb=480,
        ram_req_gb=2.0,
        wer_turkish="%5.8 WER",
        description="Kokoro-82M sentetik konuşma verisi ve Türkçe morfolojik düzeltmeyle eğitilmiş dengeli v2.1 modeli. Standart işlemciler için yüksek doğruluk ve hız.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v2-small-ct2",
        fallback_repo_id="Systran/faster-whisper-small",
        system_prompt="Türkçe ses kaydı transkripsiyonu v2.1.",
    ),
    "sesmetin-v2-tiny": ModelSpecification(
        model_id="sesmetin-v2-tiny",
        name="SesMetin-v2 Tiny (Özel Türkçe v2 Hızlı)",
        category=ModelCategory.SESMETIN,
        version="2.1.0",
        size_mb=75,
        ram_req_gb=0.8,
        wer_turkish="%8.6 WER",
        description="Akustik önişleme ve sentetik konuşma optimizasyonlu ultra hafif Türkçe modeli. Düşük donanımlı cihazlarda dahi anlık deşifre sağlar.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v2-tiny-ct2",
        fallback_repo_id="Systran/faster-whisper-tiny",
        system_prompt="Hızlı Türkçe konuşma transkripsiyonu v2.1.",
    ),

    # ------------------ SesMetin-v1 Özel Türkçe Modelleri ------------------
    "sesmetin-v1-turbo": ModelSpecification(
        model_id="sesmetin-v1-turbo",
        name="SesMetin-v1 Turbo (Türkçe Optimize)",
        category=ModelCategory.SESMETIN,
        version="1.0.0",
        size_mb=1550,
        ram_req_gb=3.5,
        wer_turkish="%4.2 WER",
        description="4 katmanlı optimize edilmiş kod çözücü mimarisi. Türkçe konuşma dili ve teknik terimlerde yüksek doğruluk.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v1-turbo-ct2",
        fallback_repo_id="Systran/faster-whisper-large-v3-turbo",
        system_prompt="Bu kayıt Türkçe konuşma içermektedir. Cümle akışına, noktalama işaretlerine ve Türkçe harflere özen gösteriniz.",
    ),
    "sesmetin-v1-small": ModelSpecification(
        model_id="sesmetin-v1-small",
        name="SesMetin-v1 Small (Türkçe Dengeli)",
        category=ModelCategory.SESMETIN,
        version="1.0.0",
        size_mb=480,
        ram_req_gb=2.0,
        wer_turkish="%5.1 WER",
        description="Hız ve doğruluk dengesi gözetilerek Türkçe veri setiyle eğitilmiş, standart işlemciler için ideal model.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v1-small-ct2",
        fallback_repo_id="Systran/faster-whisper-small",
        system_prompt="Türkçe ses kaydı transkripsiyonu. Noktalama ve imla kurallarına dikkat ediniz.",
    ),
    "sesmetin-v1-tiny": ModelSpecification(
        model_id="sesmetin-v1-tiny",
        name="SesMetin-v1 Tiny (Türkçe Ultra Hızlı)",
        category=ModelCategory.SESMETIN,
        version="1.0.0",
        size_mb=75,
        ram_req_gb=0.8,
        wer_turkish="%8.4 WER",
        description="Düşük donanımlı dizüstü bilgisayarlar ve anlık transkripsiyon için ultra hafif Türkçe modeli.",
        is_proprietary=True,
        ct2_quantization="int8",
        repo_id="The0Sanity/sesmetin-v1-tiny-ct2",
        fallback_repo_id="Systran/faster-whisper-tiny",
        system_prompt="Hızlı Türkçe konuşma transkripsiyonu.",
    ),

    # ------------------ Standart Faster-Whisper Modelleri ------------------
    "tiny": ModelSpecification(
        model_id="tiny",
        name="Faster-Whisper Tiny",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=75,
        ram_req_gb=0.8,
        wer_turkish="%10.5 WER",
        description="OpenAI Whisper resmi tiny modelinin CTranslate2 INT8 sürümü. En düşük bellek tüketimi.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-tiny",
    ),
    "base": ModelSpecification(
        model_id="base",
        name="Faster-Whisper Base",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=145,
        ram_req_gb=1.2,
        wer_turkish="%8.8 WER",
        description="Hafif ve genel amaçlı çok dilli resmi Whisper modeli.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-base",
    ),
    "small": ModelSpecification(
        model_id="small",
        name="Faster-Whisper Small",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=480,
        ram_req_gb=2.0,
        wer_turkish="%6.4 WER",
        description="Varsayılan önerilen resmi model. Orta düzey işlemcilerde akıcı çalışma ve tatminkar doğruluk.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-small",
    ),
    "medium": ModelSpecification(
        model_id="medium",
        name="Faster-Whisper Medium",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=1500,
        ram_req_gb=4.0,
        wer_turkish="%4.8 WER",
        description="Yüksek kaliteli transkripsiyon gerektiren durumlar için geniş kapasiteli resmi model.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-medium",
    ),
    "large-v3-turbo": ModelSpecification(
        model_id="large-v3-turbo",
        name="Faster-Whisper Large-v3-Turbo",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=1600,
        ram_req_gb=4.5,
        wer_turkish="%4.0 WER",
        description="En son nesil 4 kod çözücü katmanlı turbo model. Yüksek transkripsiyon doğruluğu.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-large-v3-turbo",
    ),
    "large-v3": ModelSpecification(
        model_id="large-v3",
        name="Faster-Whisper Large-v3",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=3100,
        ram_req_gb=6.0,
        wer_turkish="%3.8 WER",
        description="Tam 1550M parametreli amiral gemisi resmi Whisper modeli. Yüksek transkripsiyon hassasiyeti.",
        is_proprietary=False,
        ct2_quantization="int8",
        repo_id="Systran/faster-whisper-large-v3",
    ),
}


def get_model_spec(model_id: str) -> Optional[ModelSpecification]:
    """Belirtilen model kimliğinin özelliklerini döndürür, bulunamazsa None."""
    return MODEL_CATALOG.get(model_id)


def list_available_models(category: Optional[ModelCategory] = None) -> List[ModelSpecification]:
    """Katalogdaki modelleri listeler, kategori belirtilmişse filtreler."""
    if category is None:
        return list(MODEL_CATALOG.values())
    return [spec for spec in MODEL_CATALOG.values() if spec.category == category]
