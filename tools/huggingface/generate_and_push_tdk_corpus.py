"""SesMetin-v2 - 10M+ Turkish TDK Permutation Corpus Generator & Streaming Hub Pusher.

Generates 10,000,000+ synthetic Turkish utterances utilizing combinatorial
permutations from the official Turkish Language Association (TDK) lexicon.
Streams directly to Hugging Face Datasets in sharded Apache Parquet format (zstd)
with zero persistent local disk storage.
"""

import argparse
import io
import json
import logging
import os
import random
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from huggingface_hub import CommitOperationAdd, HfApi, get_token
    HAS_HF_HUB = True
except ImportError:
    CommitOperationAdd = None
    HfApi = None
    get_token = lambda: None
    HAS_HF_HUB = False

from tools.huggingface.tdk_lexicon import TDKLexicon

logger = logging.getLogger("TDKCorpusGenerator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REPO_ID = "The0Sanity/sesmetin-v2-tdk-10m-corpus"
SCHEMA = pa.schema([
    ("id", pa.string()),
    ("text", pa.string()),
    ("word_count", pa.int32()),
    ("has_punctuation", pa.bool_()),
    ("domain", pa.string()),
])


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


class TDKPermutationGenerator:
    """Generates procedurally permuted Turkish sentences with positional variation."""

    def __init__(self, vocabulary: Optional[List[str]] = None, seed: int = 42):
        if vocabulary is None:
            lexicon = TDKLexicon()
            vocabulary = lexicon.get_words()
        self.vocabulary = [w for w in vocabulary if len(w) >= 2]
        if len(self.vocabulary) < 4:
            raise ValueError("Vocabulary size must be at least 4 words")
        self.rng = random.Random(seed)
        self._counter = 0

    def generate_single_utterance(self) -> Dict[str, Any]:
        """Generates a single randomized Turkish utterance."""
        self._counter += 1
        item_id = f"tdk_{self._counter:08d}"

        # Sentence length averaging ~100 words (75 to 125 words)
        length = self.rng.randint(75, 125)

        # Sample words without collision in this sentence
        if length <= len(self.vocabulary):
            chosen_words = self.rng.sample(self.vocabulary, length)
        else:
            chosen_words = [self.rng.choice(self.vocabulary) for _ in range(length)]

        # Permute/shuffle order
        self.rng.shuffle(chosen_words)

        # 70% chance of punctuated/capitalized, 30% pure lowercase acoustic stream
        has_punctuation = self.rng.random() < 0.70

        if has_punctuation:
            # Build punctuated multi-clause/multi-sentence utterance
            formatted_words = []
            capitalize_next = True
            words_in_clause = 0
            clause_target = self.rng.randint(6, 13)

            for idx, w in enumerate(chosen_words):
                word_str = turkish_capitalize(w) if capitalize_next else w
                capitalize_next = False
                words_in_clause += 1

                is_last_word = (idx == len(chosen_words) - 1)
                if is_last_word:
                    terminator = self.rng.choice([".", ".", ".", "?", "!"])
                    formatted_words.append(word_str + terminator)
                elif words_in_clause >= clause_target:
                    if self.rng.random() < 0.45:
                        punct = self.rng.choice([".", ".", "?", "!"])
                        formatted_words.append(word_str + punct)
                        capitalize_next = True
                    else:
                        punct = self.rng.choice([",", ",", ";"])
                        formatted_words.append(word_str + punct)
                    words_in_clause = 0
                    clause_target = self.rng.randint(6, 13)
                else:
                    formatted_words.append(word_str)

            text = " ".join(formatted_words)
        else:
            # Pure lowercase unpunctuated acoustic stream
            text = " ".join([w.lower() for w in chosen_words])

        return {
            "id": item_id,
            "text": text,
            "word_count": length,
            "has_punctuation": has_punctuation,
            "domain": "tdk_permutation",
        }

    def generate_batch(self, size: int) -> List[Dict[str, Any]]:
        """Generates a batch of distinct utterances."""
        return [self.generate_single_utterance() for _ in range(size)]


def serialize_shard_to_parquet_bytes(data: List[Dict[str, Any]]) -> bytes:
    """Serializes a list of dictionaries into a ZSTD-compressed Parquet byte stream."""
    pylist = {
        "id": [item["id"] for item in data],
        "text": [item["text"] for item in data],
        "word_count": [item["word_count"] for item in data],
        "has_punctuation": [item["has_punctuation"] for item in data],
        "domain": [item["domain"] for item in data],
    }
    table = pa.Table.from_pydict(pylist, schema=SCHEMA)
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="zstd")
    return sink.getvalue()


def build_dataset_readme(total_samples: int = 10000000, num_shards: int = 50) -> str:
    """Generates the official declarative README.md with YAML metadata for Hugging Face Hub."""
    return f"""---
language:
- tr
license: apache-2.0
task_categories:
- automatic-speech-recognition
- text-generation
task_ids:
- language-modeling
tags:
- turkish
- tdk
- speech
- nlp
- ctranslate2
- whisper
- inverse-text-normalization
- sesmetin
pretty_name: SesMetin-v2 10M+ Turkish TDK Permutation Corpus
size_categories:
- 10M<n<100M
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/train-*.parquet"
---

# SesMetin-v2 10M+ Turkish TDK Permutation Corpus

Large-scale Turkish combinatorial speech and text corpus containing over {total_samples:,} utterances
generated from the official Turkish Language Association (TDK - Türk Dil Kurumu) Güncel Türkçe Sözlük (12th Edition).

## Dataset Summary
- **Total Utterances**: {total_samples:,} rows
- **Language**: Turkish (`tr`)
- **Lexical Source**: Official TDK Güncel Türkçe Sözlük (81,700+ clean headwords)
- **Formatting Distribution**:
  - 70% Natural Punctuation & Capitalization (normalized target)
  - 30% Pure Lowercase Acoustic Token Stream (robust phonetic decoding)
- **Sharding Architecture**: {num_shards} Apache Parquet shards with ZSTD compression.
- **Zero Local Disk Overhead**: Designed for high-throughput cloud streaming via `datasets.load_dataset(..., streaming=True)`.
- **Official Repository**: https://github.com/The0Sanity/Speech-To-Text

## Usage with Hugging Face Datasets

### 1. High-Speed Cloud Streaming (Zero Local Storage)
```python
from datasets import load_dataset

# Stream 10 million rows on the fly without downloading to local disk
dataset = load_dataset("{REPO_ID}", split="train", streaming=True)

for example in dataset.take(5):
    print(f"[ID: {{example['id']}}] {{example['text']}} (words: {{example['word_count']}})")
```

### 2. Shuffled Training Batching
```python
from datasets import load_dataset
from torch.utils.data import DataLoader

streamed = load_dataset("{REPO_ID}", split="train", streaming=True)
shuffled = streamed.shuffle(buffer_size=50_000, seed=42)
```

## Citation & Attribution
Official Speech-To-Text open source project:
https://github.com/The0Sanity/Speech-To-Text

License: Apache 2.0
"""


def prepare_shard_operation(
    shard_index: int,
    total_shards: int,
    parquet_bytes: bytes,
) -> Any:
    """Prepares an in-memory CommitOperationAdd for the given shard without disk I/O."""
    shard_name = f"train-{shard_index:05d}-of-{total_shards:05d}.parquet"
    path_in_repo = f"data/{shard_name}"
    if CommitOperationAdd is None:
        raise RuntimeError("huggingface_hub is required for CommitOperationAdd.")
    return CommitOperationAdd(
        path_in_repo=path_in_repo,
        path_or_fileobj=io.BytesIO(parquet_bytes),
    )


def commit_shard_batch(
    api: Any,
    repo_id: str,
    operations: List[Any],
    commit_message: str,
) -> bool:
    """Commits a batch of operations in a single atomic Git commit transaction."""
    if not operations:
        return True
    api.create_commit(
        repo_id=repo_id,
        repo_type="dataset",
        operations=operations,
        commit_message=commit_message,
    )
    return True


def upload_shard_in_memory(
    api: Any,
    repo_id: str,
    shard_index: int,
    total_shards: int,
    parquet_bytes: bytes,
) -> bool:
    """Uploads a single Parquet shard directly to the Hugging Face dataset repository."""
    op = prepare_shard_operation(shard_index, total_shards, parquet_bytes)
    shard_name = f"train-{shard_index:05d}-of-{total_shards:05d}.parquet"
    return commit_shard_batch(
        api=api,
        repo_id=repo_id,
        operations=[op],
        commit_message=f"feat(corpus): add shard {shard_index + 1}/{total_shards} ({shard_name})",
    )


def stream_corpus_to_huggingface(
    token: str,
    repo_id: str = REPO_ID,
    total_samples: int = 10000000,
    shard_size: int = 200000,
    max_shards: Optional[int] = None,
    start_shard: int = 0,
    batch_commit_size: int = 5,
) -> str:
    """Orchestrates generation of 10M+ examples with double-buffering and batched commits."""
    if not HAS_HF_HUB:
        raise RuntimeError("huggingface_hub package is required for uploading to Hugging Face.")

    api = HfApi(token=token)
    logger.info(f"Ensuring Hugging Face dataset repository exists: {repo_id}")
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

    total_num_shards = (total_samples + shard_size - 1) // shard_size
    num_shards = total_num_shards - start_shard
    if max_shards is not None:
        num_shards = min(num_shards, max_shards)

    # 1. Upload dataset card and YAML configs
    readme_content = build_dataset_readme(total_samples=total_samples, num_shards=total_num_shards)
    readme_op = CommitOperationAdd(
        path_in_repo="README.md",
        path_or_fileobj=io.BytesIO(readme_content.encode("utf-8")),
    )
    commit_shard_batch(
        api=api,
        repo_id=repo_id,
        operations=[readme_op],
        commit_message="docs: publish declarative Parquet metadata and dataset card",
    )

    # 2. Initialize generator
    logger.info("Initializing TDK Permutation Generator with complete TDK lexicon...")
    generator = TDKPermutationGenerator(seed=42 + start_shard)
    logger.info(f"Loaded {len(generator.vocabulary)} unique clean TDK headwords.")

    # 3. Stream shards incrementally with double-buffered commit pipelining
    logger.info(
        f"Beginning streaming of {num_shards} shards ({shard_size:,} rows per shard, "
        f"starting at shard {start_shard}, commit batch size: {batch_commit_size})..."
    )

    pending_ops: List[Any] = []
    upload_future = None
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        for shard_idx in range(start_shard, start_shard + num_shards):
            batch = generator.generate_batch(shard_size)
            parquet_bytes = serialize_shard_to_parquet_bytes(batch)
            del batch  # Immediate memory reclamation

            shard_size_mb = len(parquet_bytes) / (1024 * 1024)
            logger.info(
                f"Generated Shard {shard_idx + 1}/{total_num_shards} "
                f"({shard_size_mb:.2f} MB compressed Parquet in memory)"
            )
            op = prepare_shard_operation(shard_idx, total_num_shards, parquet_bytes)
            pending_ops.append(op)
            del parquet_bytes

            if len(pending_ops) >= batch_commit_size:
                if upload_future is not None:
                    upload_future.result()  # Wait for prior batch commit to complete

                ops_to_commit = list(pending_ops)
                pending_ops = []
                first_shard = shard_idx - len(ops_to_commit) + 2
                last_shard = shard_idx + 1
                msg = f"feat(corpus): add shards {first_shard}-{last_shard}/{total_num_shards}"
                logger.info(f"Submitting batched commit for {len(ops_to_commit)} shards ({first_shard}-{last_shard})...")
                upload_future = executor.submit(
                    commit_shard_batch,
                    api=api,
                    repo_id=repo_id,
                    operations=ops_to_commit,
                    commit_message=msg,
                )

        # Flush any in-flight background commit
        if upload_future is not None:
            upload_future.result()

        # Flush final remainder batch if any
        if pending_ops:
            first_shard = start_shard + num_shards - len(pending_ops) + 1
            last_shard = start_shard + num_shards
            msg = f"feat(corpus): add shards {first_shard}-{last_shard}/{total_num_shards}"
            logger.info(f"Submitting final remainder commit for {len(pending_ops)} shards ({first_shard}-{last_shard})...")
            commit_shard_batch(
                api=api,
                repo_id=repo_id,
                operations=pending_ops,
                commit_message=msg,
            )
            pending_ops = []

    finally:
        executor.shutdown(wait=True)

    hub_url = f"https://huggingface.co/datasets/{repo_id}"
    logger.info(f"Successfully published {num_shards} shards to Hugging Face: {hub_url}")
    return hub_url


def main():
    parser = argparse.ArgumentParser(description="10M+ Turkish TDK Permutation Corpus Hub Pusher")
    parser.add_argument("--repo-id", type=str, default=REPO_ID, help="Target Hugging Face dataset repo")
    parser.add_argument("--total-samples", type=int, default=10000000, help="Total samples to generate")
    parser.add_argument("--shard-size", type=int, default=200000, help="Samples per Parquet shard")
    parser.add_argument("--max-shards", type=int, default=None, help="Limit number of shards to process")
    parser.add_argument("--start-shard", type=int, default=0, help="Starting shard index")
    parser.add_argument("--batch-commit-size", type=int, default=5, help="Number of shards per commit transaction")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN") or (get_token() if HAS_HF_HUB else None)
    if not token:
        print("Error: HF_TOKEN environment variable or huggingface-cli login is required to publish to Hugging Face Hub.")
        sys.exit(1)

    stream_corpus_to_huggingface(
        token=token,
        repo_id=args.repo_id,
        total_samples=args.total_samples,
        shard_size=args.shard_size,
        max_shards=args.max_shards,
        start_shard=args.start_shard,
        batch_commit_size=args.batch_commit_size,
    )


if __name__ == "__main__":
    main()
