"""SesMetin-v2 - Hugging Face Cloud Training Launcher.

Submits training jobs to Hugging Face Jobs cloud infrastructure (GPU/TPU)
ensuring that the local machine performs no resource-heavy training.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi

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
    target_repo: str = "The0Sanity/sesmetin-v2-small-ct2",
) -> None:
    """Prepares and launches the training job on Hugging Face cloud infrastructure."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN environment variable is required to launch Hugging Face Jobs.")
        print("Please set your Hugging Face write token before launching.")
        sys.exit(1)

    username = check_auth(token)
    print(f"Authenticated as Hugging Face user: {username}")
    print("=" * 65)
    print("Hugging Face Cloud GPU Training Launcher")
    print(f"Cloud Hardware   : {flavor} (High-performance GPU)")
    print(f"Timeout          : {timeout}")
    print(f"Base Model       : {base_model}")
    print(f"Target Hub Repo  : {target_repo}")
    print(f"Dataset          : https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus")
    print("Host Machine Note: Zero local CPU/GPU cycles are used; all training runs on Hugging Face cloud.")
    print("=" * 65)

    script_path = BASE_DIR / "tools" / "huggingface" / "hf_train_job.py"
    if not script_path.exists():
        print(f"Error: Training script not found at {script_path}")
        sys.exit(1)

    print("\nTo submit this job directly via Hugging Face CLI, execute:")
    cli_cmd = (
        f'hf jobs uv run --flavor {flavor} --timeout {timeout} --secrets HF_TOKEN "{script_path}"'
    )
    print(f"  {cli_cmd}\n")

    print(f"Monitoring Dashboard: https://huggingface.co/{username}")
    print(f"Target Repository   : https://huggingface.co/{target_repo}")


def main():
    parser = argparse.ArgumentParser(description="SesMetin-v2 Hugging Face Cloud Training Launcher")
    parser.add_argument("--flavor", type=str, default="a10g-large", help="Hugging Face hardware flavor (e.g., a10g-large, t4-medium)")
    parser.add_argument("--timeout", type=str, default="2h", help="Job timeout limit")
    parser.add_argument("--base-model", type=str, default="openai/whisper-small", help="Base model identifier")
    parser.add_argument("--target-repo", type=str, default="The0Sanity/sesmetin-v2-small-ct2", help="Target model repository")
    args = parser.parse_args()

    launch_job(
        flavor=args.flavor,
        timeout=args.timeout,
        base_model=args.base_model,
        target_repo=args.target_repo,
    )


if __name__ == "__main__":
    main()
