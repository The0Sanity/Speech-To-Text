"""Yerel model depolaması, indirme, silme ve disk alanı yöneticisi."""

import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.hardware import format_memory_size
from src.models.catalog import (
    LEGACY_MODEL_IDS,
    LEGACY_REPO_IDS,
    MODEL_CATALOG,
    ModelSpecification,
    get_model_spec,
    resolve_model_id,
)


class ModelManager:
    """ASR modellerinin yerel depolama ve indirme durumunu yönetir."""

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            from src.config import MODELS_DIR
            self.models_dir = Path(MODELS_DIR)
        else:
            self.models_dir = Path(models_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)

    def _get_candidate_paths(self, model_id: str) -> List[Path]:
        """Bir model kimliği için olası yerel depolama dizin yollarını döndürür."""
        model_id = resolve_model_id(model_id)
        legacy_ids = [old for old, new in LEGACY_MODEL_IDS.items() if new == model_id]
        candidates = [self.models_dir / name for name in [model_id, *legacy_ids]]

        spec = get_model_spec(model_id)
        repos = ([spec.repo_id] if spec and spec.repo_id else []) + LEGACY_REPO_IDS.get(model_id, [])
        for repo in repos:
            # Hugging Face hub önbellek formatı (örn: models--Systran--faster-whisper-small)
            candidates.append(self.models_dir / f"models--{repo.replace('/', '--')}")

        return candidates

    def find_local_model_dir(self, model_id: str) -> Optional[Path]:
        """The folder holding this model's model.bin, wherever a current or older version put it."""
        for path in self._get_candidate_paths(model_id):
            if not path.is_dir():
                continue
            if (path / "model.bin").exists():
                return path
            for snap in sorted((path / "snapshots").glob("*")):
                if (snap / "model.bin").exists():
                    return snap
        return None

    def is_model_installed(self, model_id: str) -> bool:
        """Modelin yerel dizinde mevcut ve kullanıma hazır olup olmadığını denetler."""
        return self.find_local_model_dir(model_id) is not None

    def get_installed_models(self) -> List[str]:
        """Yerel olarak indirilmiş ve hazır olan tüm model kimliklerini döndürür."""
        installed = []
        for model_id in MODEL_CATALOG:
            if self.is_model_installed(model_id):
                installed.append(model_id)
        return installed

    def get_storage_usage(self) -> Dict[str, Any]:
        """Modeller dizininin diskte kapladığı toplam alanı ve boş disk alanını hesaplar."""
        used_bytes = 0
        if self.models_dir.exists():
            for root, _, files in os.walk(self.models_dir):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        used_bytes += os.path.getsize(fp)
                    except (OSError, FileNotFoundError):
                        pass

        free_bytes = 0
        try:
            total, used, free = shutil.disk_usage(str(self.models_dir))
            free_bytes = free
        except Exception:
            free_bytes = 100 * 1024 * 1024 * 1024  # 100 GB varsayılan

        return {
            "used_bytes": used_bytes,
            "used_formatted": format_memory_size(used_bytes),
            "free_bytes": free_bytes,
            "free_formatted": format_memory_size(free_bytes),
        }

    def delete_model(self, model_id: str) -> bool:
        """Model dizinini ve önbelleğini güvenli biçimde siler."""
        deleted = False
        for path in self._get_candidate_paths(model_id):
            if path.exists():
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    deleted = True
                except OSError:
                    pass
        return deleted

    def download_model(
        self,
        model_id: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> bool:
        """Belirtilen modeli arka planda indirir.
        
        Faster-Whisper veya Hugging Face üzerinden indirme yapar.
        """
        spec = get_model_spec(model_id)
        if not spec:
            raise ValueError(f"Geçersiz model kimliği: {model_id}")

        if progress_callback:
            progress_callback(0.05, f"{spec.name} indirmesi başlatılıyor...")

        model_id = spec.model_id
        target_dir = self.models_dir / model_id
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            from faster_whisper import download_model as fw_download_model
            # İptal kontrolü
            if cancel_event and cancel_event.is_set():
                self.delete_model(model_id)
                return False

            if progress_callback:
                progress_callback(0.30, f"{spec.name} ağırlıkları indiriliyor...")

            # No substitute model on failure: the error reaches the caller and the user sees it.
            repo_or_name = spec.repo_id if spec.repo_id else model_id
            fw_download_model(repo_or_name, output_dir=str(target_dir))
            if not list(target_dir.glob("**/model.bin")):
                raise RuntimeError(f"Model deposunda ({repo_or_name}) ikili agirliklar (model.bin) bulunamadi.")

            if progress_callback:
                progress_callback(1.0, f"{spec.name} basariyla kuruldu ve hazir.")
            return True

        except Exception as e:
            # Hata durumunda yarim kalan dosyalari temizle
            if cancel_event and cancel_event.is_set():
                self.delete_model(model_id)
                return False

            if progress_callback:
                progress_callback(0.0, f"Indirme hatasi: {e}")
            raise e
