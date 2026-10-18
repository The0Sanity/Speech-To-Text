"""SesMetin-v2 - Hugging Face Cloud Training Launcher.

Submits training jobs to Hugging Face Jobs cloud infrastructure (GPU/TPU)
ensuring that the local machine performs no resource-heavy training.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi, get_token

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def check_auth(token: str) -> str:
    """Verifies Hugging Face authentication and returns username."""
    api = HfApi(token=token)
    user_info = api.whoami()
    return user_info["name"]


def launch_job(
    flavor: str = "a10g-large",
    timeout: str = "2h",
    base_model: str = "openai/whisper-small",
    teacher_model: str = "openai/whisper-large-v3",
    distillation: bool = True,
    prune_turkish_vocab: bool = True,
    target_repo: str = "The0Sanity/sesmetin-v2-small-ct2",
    job_type: str = "train",
) -> None:
    """Prepares and launches the training or dataset job on Hugging Face cloud infrastructure."""
    token = os.environ.get("HF_TOKEN") or get_token()
    if not token:
        print("Error: HF_TOKEN environment variable or huggingface-cli login is required.")
        print("Please authenticate using 'hf auth login' or set HF_TOKEN before launching.")
        sys.exit(1)

    username = check_auth(token)
    print(f"Authenticated as Hugging Face user: {username}")
    print("=" * 65)

    if job_type == "generate-tdk-corpus":
        script_path = BASE_DIR / "tools" / "huggingface" / "cloud_tdk_10m_job.py"
        flavor = "cpu-upgrade" if flavor == "a10g-large" else flavor
        print("Hugging Face Cloud 10M+ TDK Dataset Generator Launcher")
        print(f"Cloud Hardware   : {flavor} (High-throughput CPU/RAM)")
        print(f"Timeout          : {timeout}")
        print(f"Target Hub Repo  : https://huggingface.co/datasets/The0Sanity/sesmetin-v2-tdk-10m-corpus")
        print("Host Machine Note: Zero local CPU/GPU cycles are used; all 10M rows generate on cloud.")
    else:
        script_path = BASE_DIR / "tools" / "huggingface" / "hf_train_job.py"
        print("Hugging Face Cloud GPU Training Launcher")
        print(f"Cloud Hardware   : {flavor} (High-performance GPU)")
        print(f"Timeout          : {timeout}")
        print(f"Base Model       : {base_model}")
        print(f"Teacher Model    : {teacher_model if distillation else 'N/A'}")
        print(f"Distillation     : {'Enabled' if distillation else 'Disabled'}")
        print(f"Vocab Pruning    : {'Enabled (Turkish ~12k tokens)' if prune_turkish_vocab else 'Disabled'}")
        print(f"Target Hub Repo  : {target_repo}")
        print(f"Dataset          : https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus")
        print("Host Machine Note: Zero local CPU/GPU cycles are used; all training runs on Hugging Face cloud.")
    print("=" * 65)

    if not script_path.exists():
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    print("\nTo submit this job directly via Hugging Face CLI, execute:")
    cli_flags = f'--flavor {flavor} --timeout {timeout} --secrets HF_TOKEN "{script_path}"'
    if job_type == "train":
        extra_flags = f' -- --base-model "{base_model}"'
        if distillation:
            extra_flags += f' --teacher-model "{teacher_model}" --distillation'
        if prune_turkish_vocab:
            extra_flags += ' --prune-turkish-vocab'
        cli_flags += extra_flags

    cli_cmd = f"hf jobs uv run {cli_flags}"
    print(f"  {cli_cmd}\n")

    print(f"Monitoring Dashboard: https://huggingface.co/{username}")
    print(f"Target Repository   : https://huggingface.co/{target_repo}")


def main():
    parser = argparse.ArgumentParser(description="SesMetin-v2 Hugging Face Cloud Job Launcher")
    parser.add_argument("--job-type", type=str, choices=["train", "generate-tdk-corpus"], default="train", help="Type of cloud job")
    parser.add_argument("--flavor", type=str, default="a10g-large", help="Hugging Face hardware flavor (e.g., a10g-large, cpu-upgrade)")
    parser.add_argument("--timeout", type=str, default="2h", help="Job timeout limit")
    parser.add_argument("--base-model", type=str, default="openai/whisper-small", help="Base model identifier")
    parser.add_argument("--teacher-model", type=str, default="openai/whisper-large-v3", help="Teacher model identifier for distillation")
    parser.add_argument("--no-distillation", dest="distillation", action="store_false", help="Disable knowledge distillation")
    parser.add_argument("--no-prune-vocab", dest="prune_turkish_vocab", action="store_false", help="Disable Turkish vocabulary pruning")
    parser.add_argument("--target-repo", type=str, default="The0Sanity/sesmetin-v2-small-ct2", help="Target model repository")
    args = parser.parse_args()

    launch_job(
        flavor=args.flavor,
        timeout=args.timeout,
        base_model=args.base_model,
        teacher_model=args.teacher_model,
        distillation=args.distillation,
        prune_turkish_vocab=args.prune_turkish_vocab,
        target_repo=args.target_repo,
        job_type=args.job_type,
    )


if __name__ == "__main__":
    main()
