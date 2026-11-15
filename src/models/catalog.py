"""SesMetin Pro model kataloğu ve model özellikleri tanımları."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ModelCategory(str, Enum):
    """Model kategorisi. SESMETIN is kept for old callers; no model is in it any more."""
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
    files: List[str] = field(default_factory=lambda: ["model.bin", "config.json", "vocabulary.json"])


# Word error rates are measured, not claimed: docs/BENCHMARKS.md (FLEURS Turkish, 150 clips).
NOT_MEASURED = "Ölçülmedi"

MODEL_CATALOG: Dict[str, ModelSpecification] = {
    "tiny": ModelSpecification(
        model_id="tiny",
        name="Faster-Whisper Tiny",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=75,
        ram_req_gb=0.8,
        wer_turkish="%41.1 (FLEURS)",
        description="OpenAI Whisper resmi tiny modelinin CTranslate2 INT8 sürümü. En düşük bellek tüketimi.",
        repo_id="Systran/faster-whisper-tiny",
    ),
    "base": ModelSpecification(
        model_id="base",
        name="Faster-Whisper Base",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=145,
        ram_req_gb=1.2,
        wer_turkish=NOT_MEASURED,
        description="Hafif ve genel amaçlı çok dilli resmi Whisper modeli.",
        repo_id="Systran/faster-whisper-base",
    ),
    "small": ModelSpecification(
        model_id="small",
        name="Faster-Whisper Small",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=480,
        ram_req_gb=2.0,
        wer_turkish="%15.2 (FLEURS)",
        description="Varsayılan önerilen resmi model. Orta düzey işlemcilerde akıcı çalışır.",
        repo_id="Systran/faster-whisper-small",
    ),
    "medium": ModelSpecification(
        model_id="medium",
        name="Faster-Whisper Medium",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=1500,
        ram_req_gb=4.0,
        wer_turkish=NOT_MEASURED,
        description="Daha yüksek doğruluk gerektiren durumlar için geniş kapasiteli resmi model.",
        repo_id="Systran/faster-whisper-medium",
    ),
    "large-v3-turbo": ModelSpecification(
        model_id="large-v3-turbo",
        name="Faster-Whisper Large-v3-Turbo",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=1600,
        ram_req_gb=4.5,
        wer_turkish=NOT_MEASURED,
        description="4 kod çözücü katmanlı turbo model.",
        repo_id="mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    ),
    "large-v3": ModelSpecification(
        model_id="large-v3",
        name="Faster-Whisper Large-v3",
        category=ModelCategory.WHISPER,
        version="official",
        size_mb=3100,
        ram_req_gb=6.0,
        wer_turkish=NOT_MEASURED,
        description="Tam 1550M parametreli resmi Whisper modeli.",
        repo_id="Systran/faster-whisper-large-v3",
    ),
}

# Model ids that older versions offered. The v2 files were byte-identical copies of the stock
# models below and the v1 repositories never existed, so old settings map to the real model.
LEGACY_MODEL_IDS: Dict[str, str] = {
    "sesmetin-v2-turbo": "large-v3-turbo",
    "sesmetin-v2-small": "small",
    "sesmetin-v2-tiny": "tiny",
    "sesmetin-v1-turbo": "large-v3-turbo",
    "sesmetin-v1-small": "small",
    "sesmetin-v1-tiny": "tiny",
}

# Where older versions stored those copies; a download found there is reused, not fetched again.
LEGACY_REPO_IDS: Dict[str, List[str]] = {
    "large-v3-turbo": ["The0Sanity/sesmetin-v2-turbo-ct2", "Systran/faster-whisper-large-v3-turbo"],
    "small": ["The0Sanity/sesmetin-v2-small-ct2"],
    "tiny": ["The0Sanity/sesmetin-v2-tiny-ct2"],
}


def resolve_model_id(model_id: str) -> str:
    """Maps a model id from an older version's settings to the current catalog id."""
    return LEGACY_MODEL_IDS.get(model_id, model_id)


def get_model_spec(model_id: str) -> Optional[ModelSpecification]:
    """Belirtilen model kimliğinin özelliklerini döndürür, bulunamazsa None."""
    return MODEL_CATALOG.get(resolve_model_id(model_id))


def list_available_models(category: Optional[ModelCategory] = None) -> List[ModelSpecification]:
    """Katalogdaki modelleri listeler, kategori belirtilmişse filtreler."""
    if category is None:
        return list(MODEL_CATALOG.values())
    return [spec for spec in MODEL_CATALOG.values() if spec.category == category]
