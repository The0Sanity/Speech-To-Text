"""Release guard: the tag being published must equal the version built into the app.

A mismatch ships an exe that reports an older version than its release, so the
app offers the same update forever. Prints the app version on success.

Usage: python scripts/check_version_sync.py --tag v1.1.6
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _find(path: str, pattern: str) -> str:
    match = re.search(pattern, (ROOT / path).read_text(encoding="utf-8"))
    if not match:
        sys.exit(f"version not found in {path}")
    return ".".join(match.groups())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    tag = parser.parse_args().tag.lstrip("vV")

    versions = {
        "src/config.py": _find("src/config.py", r'APP_VERSION = "(\d+)\.(\d+)\.(\d+)"'),
        "src/__init__.py": _find("src/__init__.py", r'__version__ = "(\d+)\.(\d+)\.(\d+)"'),
        "version_info.txt": _find("version_info.txt", r"filevers=\((\d+), (\d+), (\d+), 0\)"),
    }
    wrong = {path: v for path, v in versions.items() if v != tag}
    if wrong:
        sys.exit(f"release tag is {tag} but these files say otherwise: {wrong}")
    print(tag)


if __name__ == "__main__":
    main()
