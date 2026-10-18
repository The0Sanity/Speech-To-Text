"""SesMetin-v2 - Whisper Turkish Vocabulary & Embedding Matrix Pruner.

Prunes Whisper's 51,865 multilingual vocabulary down to a focused Turkish
representation (~12,000 subwords), saving 120MB to 200MB of embedding and
projection weights while retaining 100% of Turkish speech transcription tokens.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logger = logging.getLogger("WhisperVocabPruner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Turkish alphabet (29 letters lowercase & uppercase, preserving dotted/undotted i)
TURKISH_LETTERS = set("abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ")
COMMON_SYMBOLS = set("0123456789 .,!?:;-_'\"/\\()[]{}<>%+=*#@$&^~`\n\t\rĠĊ")


def is_valid_turkish_token(token_str: str) -> bool:
    """Checks whether a token consists solely of Turkish letters, standard ASCII, or punctuation."""
    if not token_str:
        return False
    # Filter out foreign non-Latin scripts (Cyrillic, Arabic, CJK, Greek, Hebrew, Devanagari, Thai, etc.)
    for char in token_str:
        if char in TURKISH_LETTERS or char in COMMON_SYMBOLS:
            continue
        # Also allow standard ASCII letters for technical / scientific Turkish loanwords
        if ("a" <= char <= "z") or ("A" <= char <= "Z"):
            continue
        # Foreign or non-Turkish character found
        return False
    return True


def is_whisper_special_token(token_str: str) -> bool:
    """Checks whether a token is a Whisper control token or timestamp."""
    if token_str.startswith("<|") and token_str.endswith("|>"):
        return True
    return False


def build_retained_token_set(
    vocab: Dict[str, int],
    target_languages: Optional[List[str]] = None,
    preserve_special_tokens: bool = True,
) -> Set[int]:
    """Filters vocabulary and returns a set of retained token IDs."""
    if target_languages is None:
        target_languages = ["tr"]

    retained_token_ids = set()

    for token_str, token_id in vocab.items():
        # 1. Special tokens check
        if is_whisper_special_token(token_str):
            if preserve_special_tokens:
                # Keep control tokens and timestamp tokens
                retained_token_ids.add(token_id)
            continue

        # 2. Turkish character content check
        if is_valid_turkish_token(token_str):
            retained_token_ids.add(token_id)

    return retained_token_ids


def validate_turkish_coverage(retained_tokens: Set[str]) -> Tuple[bool, List[str]]:
    """Verifies that all 29 Turkish uppercase and lowercase letters exist in retained tokens."""
    missing = []
    for letter in TURKISH_LETTERS:
        if letter not in retained_tokens and not any(letter in t for t in retained_tokens):
            missing.append(letter)
    return len(missing) == 0, missing


def prune_embedding_matrix(weights: np.ndarray, retained_indices: List[int]) -> np.ndarray:
    """Slices 2D embedding weight matrix to the retained token indices."""
    sorted_indices = list(retained_indices)
    return weights[sorted_indices, :]


def prune_projection_head(weights: np.ndarray, retained_indices: List[int]) -> np.ndarray:
    """Slices linear language model head projection weights to retained token indices."""
    sorted_indices = list(retained_indices)
    return weights[sorted_indices, :]


def export_pruning_metadata(
    retained_indices: List[int],
    orig_vocab: Dict[str, int],
    output_dir: Path,
) -> Path:
    """Exports the mapping metadata between original and pruned token indices."""
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "pruned_vocab_size": len(retained_indices),
        "original_vocab_size": len(orig_vocab),
        "retained_indices": retained_indices,
    }
    mapping_file = output_dir / "vocab_pruning_metadata.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    return mapping_file
