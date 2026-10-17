"""SHA-256 Sample Registry for tracking and ensuring zero data leakage in benchmarks.

Guarantees that test datasets never duplicate sentences used in training or
previous benchmark runs.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def normalize_text_for_hash(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
    cleaned = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", " ", text.lower())
    return " ".join(cleaned.split())


def compute_sha256(text: str) -> str:
    """Compute the SHA-256 hexadecimal digest of normalized text."""
    normalized = normalize_text_for_hash(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class SampleRegistry:
    """Persistent registry of evaluated and training speech sample hashes."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.training_hashes: Set[str] = set()
        self.benchmark_hashes: Set[str] = set()
        self.metadata: Dict[str, Dict[str, str]] = {}
        if self.storage_path and self.storage_path.exists():
            self.load()

    def register_sample(self, text: str, split: str = "benchmark") -> Tuple[bool, str]:
        """Register a sentence into the registry.

        Returns:
            Tuple of (success: bool, reason: str).
            If duplicate or leaked from training, success is False.
        """
        digest = compute_sha256(text)

        if split == "benchmark":
            if digest in self.training_hashes:
                return False, "leakage_from_training"
            if digest in self.benchmark_hashes:
                return False, "duplicate_benchmark"
            self.benchmark_hashes.add(digest)
            self.metadata[digest] = {"split": "benchmark", "text": text}
            return True, "registered"

        elif split == "train":
            self.training_hashes.add(digest)
            self.metadata[digest] = {"split": "train", "text": text}
            return True, "registered"

        return False, "invalid_split"

    def is_seen(self, text: str) -> bool:
        """Check if text was already registered under training or benchmark."""
        digest = compute_sha256(text)
        return (digest in self.training_hashes) or (digest in self.benchmark_hashes)

    def import_training_corpus(self, sentences: List[str]) -> int:
        """Bulk register training sentences to guarantee zero leakage."""
        added = 0
        for s in sentences:
            success, _ = self.register_sample(s, split="train")
            if success:
                added += 1
        return added

    def save(self):
        """Persist registered hashes and metadata to disk."""
        if not self.storage_path:
            return
        os.makedirs(self.storage_path.parent, exist_ok=True)
        payload = {
            "training_hashes": list(self.training_hashes),
            "benchmark_hashes": list(self.benchmark_hashes),
            "total_registered": len(self.training_hashes) + len(self.benchmark_hashes),
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def load(self):
        """Load registered hashes from storage path."""
        if not self.storage_path or not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.training_hashes = set(payload.get("training_hashes", []))
            self.benchmark_hashes = set(payload.get("benchmark_hashes", []))
        except Exception:
            pass

    def __len__(self) -> int:
        return len(self.training_hashes) + len(self.benchmark_hashes)
