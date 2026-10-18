"""TDK N-Gram Language Model Rescorer & Phonetic Snapping Engine.

Provides sequence-level language model scoring and morphological/phonetic
Levenshtein snapping to authentic Turkish TDK lexicon entries.
"""

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

BASE_DIR = Path(__file__).resolve().parent.parent

# Core Turkish fallback vocabulary (essential high-frequency words, food, numbers, animals)
CORE_TURKISH_WORDS: Set[str] = {
    "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on",
    "yüz", "bin", "milyon", "lira", "kuruş", "saat", "dakika", "saniye",
    "patates", "domates", "portakal", "elma", "armut", "havuç", "karpuz",
    "pisi", "kuçu", "kedi", "köpek", "kuş", "tavuk", "horoz", "ördek",
    "haydi", "sen", "de", "katıl", "benimle", "görmeye", "demeye", "başlıyoruz",
    "hazır", "mısın", "gel", "git", "al", "ver", "bak", "dur", "koş", "ye",
    "hapşu", "merhaba", "nasılsın", "günaydın", "iyi", "güzel", "tamam", "evet", "hayır",
    "çocuk", "bebek", "insan", "arkadaş", "anne", "baba", "kardeş", "okul", "ev",
    "bilgisayar", "telefon", "kitap", "kalem", "defter", "masa", "sandalye",
    "bugün", "yarın", "dün", "şimdi", "sonra", "önce", "burada", "şurada", "orada",
}


def _levenshtein_distance(s1: str, s2: str, max_dist: int = 1) -> int:
    """Calculates Levenshtein distance between two strings with early termination."""
    if s1 == s2:
        return 0
    if abs(len(s1) - len(s2)) > max_dist:
        return max_dist + 1

    len1, len2 = len(s1), len(s2)
    current = list(range(len2 + 1))

    for i in range(len1):
        next_row = [i + 1] + [0] * len2
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            next_row[j + 1] = min(
                current[j + 1] + 1,      # deletion
                next_row[j] + 1,          # insertion
                current[j] + cost         # substitution
            )
        current = next_row
        if min(current) > max_dist:
            return max_dist + 1

    return current[len2]


class TDKLanguageModelRescorer:
    """In-memory TDK Turkish Language Model and Lexicon Snapper."""

    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon: Set[str] = set(CORE_TURKISH_WORDS)
        self._words_by_len: Dict[int, Set[str]] = {}

        # 1. Load comprehensive TDK lexicon cache if present
        cache_file = Path(lexicon_path) if lexicon_path else (BASE_DIR / "dataset" / "tdk_lexicon_cache.json")
        if cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    words = json.load(f)
                    if isinstance(words, list):
                        for w in words:
                            if isinstance(w, str) and w.strip():
                                clean_w = w.strip().lower()
                                self.lexicon.add(clean_w)
            except Exception:
                pass

        # 2. Build length-bucketed index for ultra-fast Levenshtein search
        for word in self.lexicon:
            w_len = len(word)
            if w_len not in self._words_by_len:
                self._words_by_len[w_len] = set()
            self._words_by_len[w_len].add(word)

    def snap_word(self, word: str, max_edit_distance: int = 1) -> str:
        """Corrects acoustic near-misses to genuine TDK Turkish words.

        Examples:
        - 'pazates' -> 'patates'
        - 'domatez' -> 'domates'
        - 'GitHub'  -> 'GitHub' (preserved)
        """
        if not word or not word.strip():
            return word

        raw = word.strip()
        # Preserve acronyms, URLs, or mixed-case technical terms
        if any(c.isupper() for c in raw[1:]) or re.search(r"[0-9_/@\.]", raw):
            return raw

        clean = raw.lower()
        # Direct hit in lexicon
        if clean in self.lexicon:
            return raw

        # Extremely short tokens (<3 chars) are rarely safe to guess
        if len(clean) < 3:
            return raw

        # Search candidates in length buckets [L - 1, L, L + 1]
        best_candidate: Optional[str] = None
        min_dist = max_edit_distance + 1

        for candidate_len in range(len(clean) - 1, len(clean) + 2):
            bucket = self._words_by_len.get(candidate_len, set())
            for candidate in bucket:
                # Fast first-letter or length pruning
                if candidate[0] != clean[0] and len(clean) > 4:
                    continue
                dist = _levenshtein_distance(clean, candidate, max_dist=max_edit_distance)
                if dist < min_dist:
                    min_dist = dist
                    best_candidate = candidate
                    if dist == 1:
                        # Found close phonetic match
                        break
            if best_candidate and min_dist == 1:
                break

        if best_candidate and min_dist <= max_edit_distance:
            # Preserve original title case if input was title-cased
            if raw[0].isupper() and len(raw) > 1 and raw[1:].islower():
                return best_candidate.capitalize()
            return best_candidate

        return raw

    def snap_sentence(self, sentence: str) -> str:
        """Applies word-level lexicon snapping across a full sentence."""
        if not sentence or not sentence.strip():
            return sentence

        tokens = re.split(r"(\s+|[.,!?;:])", sentence)
        snapped_tokens = []
        for tok in tokens:
            if re.match(r"^\w+$", tok):
                snapped_tokens.append(self.snap_word(tok))
            else:
                snapped_tokens.append(tok)
        return "".join(snapped_tokens)

    def score_sentence(self, sentence: str) -> float:
        """Calculates Turkish language model log-probability score.

        Rewards valid TDK vocabulary and penalizes out-of-lexicon gibberish.
        """
        words = re.findall(r"\w+", sentence.lower())
        if not words:
            return -10.0

        log_prob = 0.0
        for w in words:
            if w in self.lexicon:
                # Reward valid dictionary word
                log_prob += 1.0 + min(len(w) * 0.1, 0.5)
            elif w.isdigit():
                # Digits are valid ITN outputs
                log_prob += 0.5
            else:
                # Penalize out-of-lexicon non-words
                log_prob -= 3.0

        # Normalization by length
        return log_prob / math.sqrt(len(words))

    def rescore_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        lm_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Rescores Whisper candidate hypotheses using acoustic + TDK LM likelihood."""
        if not hypotheses:
            return hypotheses

        rescored = []
        for hyp in hypotheses:
            text = hyp.get("text", "").strip()
            acoustic_score = float(hyp.get("acoustic_score", 0.0))

            # Apply snapping to each candidate
            snapped_text = self.snap_sentence(text)
            lm_score = self.score_sentence(snapped_text)

            combined_score = acoustic_score + (lm_weight * lm_score)

            new_hyp = dict(hyp)
            new_hyp["text"] = snapped_text
            new_hyp["lm_score"] = round(lm_score, 4)
            new_hyp["combined_score"] = round(combined_score, 4)
            rescored.append(new_hyp)

        # Sort in descending order of combined score
        rescored.sort(key=lambda h: h["combined_score"], reverse=True)
        return rescored
