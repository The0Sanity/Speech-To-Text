# /// script
# dependencies = [
#     "pyarrow>=15.0.0",
#     "huggingface_hub>=0.23.0",
#     "trackio",
# ]
# ///

"""SesMetin-v2 - Hugging Face Cloud Job: 10M+ Turkish TDK Corpus Generator.

Executes on Hugging Face Jobs cloud infrastructure (CPU Upgrade flavor).
Generates over 10,000,000 Turkish combinatorial utterances from the official TDK
Güncel Türkçe Sözlük lexicon and streams them directly into sharded Parquet files
on Hugging Face Hub with zero local machine compute or network overhead.

Usage:
  hf jobs uv run --flavor cpu-upgrade --timeout 4h --secrets HF_TOKEN tools/huggingface/cloud_tdk_10m_job.py
"""

import argparse
import io
import json
import logging
import os
import random
import re
import sys
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, login

logger = logging.getLogger("CloudTDK10MJob")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_REPO_ID = "The0Sanity/sesmetin-v2-tdk-10m-corpus"
SCHEMA = pa.schema([
    ("id", pa.string()),
    ("text", pa.string()),
    ("word_count", pa.int32()),
    ("has_punctuation", pa.bool_()),
    ("domain", pa.string()),
])

TDK_REMOTE_URL = (
    "https://raw.githubusercontent.com/ogun/guncel-turkce-sozluk/master/sozluk/v12/src/v12.autocomplete.json"
)


def turkish_capitalize(word: str) -> str:
    """Proper Turkish capitalization handling dotted and undotted i."""
    if not word:
        return word
    first = word[0]
    rest = word[1:]
    if first == "i":
        return "İ" + rest
    if first == "ı":
        return "I" + rest
    return first.upper() + rest


def fetch_clean_tdk_vocabulary() -> List[str]:
    """Fetches and cleans official TDK words inside the cloud environment."""
    logger.info(f"Downloading TDK Güncel Türkçe Sözlük lexicon from: {TDK_REMOTE_URL}")
    req = urllib.request.Request(
        TDK_REMOTE_URL,
        headers={"User-Agent": "SesMetin-Cloud-TDKJob/1.0 (+https://github.com/The0Sanity/Speech-To-Text)"},
    )
    words = []
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                raw_word = item.get("madde", "") if isinstance(item, dict) else str(item)
                cleaned = raw_word.strip().lower()
                cleaned = re.sub(r"[\"\'\(\)\[\]\{\}\.\,\:\;\!\?]", "", cleaned)
                cleaned = re.sub(r"^-+", "", cleaned)
                if re.match(r"^[abcçdefgğhıijklmnoöprsştuüvyzâîû\s\-]+$", cleaned) and len(cleaned) >= 2:
                    for sub_w in cleaned.split():
                        if len(sub_w) >= 2:
                            words.append(sub_w)
    except Exception as e:
        logger.error(f"Failed to fetch remote TDK words: {e}")

    unique_words = sorted(list(set(words)))
    logger.info(f"Loaded {len(unique_words):,} unique valid TDK headwords.")
    return unique_words


def generate_shard_batch(
    vocabulary: List[str],
    shard_index: int,
    shard_size: int,
    seed: int,
) -> List[Dict[str, Any]]:
    """Generates a batch of distinct permuted sentences for a shard."""
    rng = random.Random(seed + shard_index)
    start_id = shard_index * shard_size
    batch = []

    for i in range(shard_size):
        item_id = f"tdk_{start_id + i + 1:08d}"
        length = rng.randint(75, 125)

        if length <= len(vocabulary):
            chosen = rng.sample(vocabulary, length)
        else:
            chosen = [rng.choice(vocabulary) for _ in range(length)]
        rng.shuffle(chosen)

        has_punctuation = rng.random() < 0.70
        if has_punctuation:
            formatted = []
            capitalize_next = True
            words_in_clause = 0
            clause_target = rng.randint(6, 13)

            for idx, w in enumerate(chosen):
                word_str = turkish_capitalize(w) if capitalize_next else w
                capitalize_next = False
                words_in_clause += 1

                is_last_word = (idx == len(chosen) - 1)
                if is_last_word:
                    terminator = rng.choice([".", ".", ".", "?", "!"])
                    formatted.append(word_str + terminator)
                elif words_in_clause >= clause_target:
                    if rng.random() < 0.45:
                        punct = rng.choice([".", ".", "?", "!"])
                        formatted.append(word_str + punct)
                        capitalize_next = True
                    else:
                        punct = rng.choice([",", ",", ";"])
                        formatted.append(word_str + punct)
                    words_in_clause = 0
                    clause_target = rng.randint(6, 13)
                else:
                    formatted.append(word_str)

            text = " ".join(formatted)
        else:
            text = " ".join([w.lower() for w in chosen])

        batch.append({
            "id": item_id,
            "text": text,
            "word_count": length,
            "has_punctuation": has_punctuation,
            "domain": "tdk_permutation",
        })

    return batch


def main():
    parser = argparse.ArgumentParser(description="SesMetin-v2 Cloud TDK 10M+ Corpus Generator")
    parser.add_argument("--repo-id", type=str, default=DEFAULT_REPO_ID, help="Target Hugging Face dataset repo")
    parser.add_argument("--total-samples", type=int, default=10000000, help="Total samples to generate")
    parser.add_argument("--shard-size", type=int, default=200000, help="Samples per shard")
    parser.add_argument("--max-shards", type=int, default=None, help="Limit number of shards (for testing)")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        login(token=hf_token)
        api = HfApi(token=hf_token)
        logger.info("Successfully authenticated with Hugging Face Hub token.")
    else:
        logger.warning("HF_TOKEN not detected in environment. Uploads may fail.")
        api = HfApi()

    logger.info("=" * 65)
    logger.info("Starting SesMetin-v2 10M+ TDK Cloud Corpus Generation")
    logger.info(f"Target Repository : https://huggingface.co/datasets/{args.repo_id}")
    logger.info(f"Total Utterances  : {args.total_samples:,}")
    logger.info(f"Shard Size        : {args.shard_size:,}")
    logger.info("Environment       : Hugging Face Cloud Jobs (Zero local resource consumption)")
    logger.info("=" * 65)

    api.create_repo(repo_id=args.repo_id, repo_type="dataset", exist_ok=True)

    vocab = fetch_clean_tdk_vocabulary()
    if len(vocab) < 100:
        logger.error("Vocabulary extraction yielded insufficient words.")
        sys.exit(1)

    num_shards = (args.total_samples + args.shard_size - 1) // args.shard_size
    if args.max_shards is not None:
        num_shards = min(num_shards, args.max_shards)

    for shard_idx in range(num_shards):
        logger.info(f"Generating Shard {shard_idx + 1}/{num_shards} ({args.shard_size:,} rows)...")
        data = generate_shard_batch(vocab, shard_idx, args.shard_size, seed=42)

        pylist = {
            "id": [item["id"] for item in data],
            "text": [item["text"] for item in data],
            "word_count": [item["word_count"] for item in data],
            "has_punctuation": [item["has_punctuation"] for item in data],
            "domain": [item["domain"] for item in data],
        }
        del data

        table = pa.Table.from_pydict(pylist, schema=SCHEMA)
        del pylist

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            pq.write_table(table, tmp_path, compression="zstd")
            del table

            shard_name = f"train-{shard_idx:05d}-of-{num_shards:05d}.parquet"
            logger.info(f"Uploading Shard {shard_idx + 1}/{num_shards} ({shard_name}) to Hub...")
            api.upload_file(
                path_or_fileobj=tmp_path,
                path_in_repo=f"data/{shard_name}",
                repo_id=args.repo_id,
                repo_type="dataset",
                commit_message=f"feat(corpus): add cloud-generated shard {shard_idx + 1}/{num_shards}",
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    logger.info("10M+ Turkish TDK Permutation Corpus generation completed successfully on cloud infrastructure!")


if __name__ == "__main__":
    main()
