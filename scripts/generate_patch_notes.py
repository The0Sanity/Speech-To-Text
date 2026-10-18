#!/usr/bin/env python3
"""
Automated Patch Notes Generator for GitHub Releases.
Extracts release notes from CHANGELOG.md or synthesizes them from git history.
Strictly adheres to zero-emoji formatting and prominent visual attribution.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def has_emojis(text: str) -> bool:
    """Checks whether the given text contains Unicode emoji characters."""
    # Common Unicode emoji ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251]"
    )
    return bool(emoji_pattern.search(text))


def strip_emojis(text: str) -> str:
    """Removes all emoji characters from text."""
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251]"
    )
    return emoji_pattern.sub("", text)


def extract_from_changelog(changelog_path: Path, tag: str) -> Optional[str]:
    """Extracts release notes for the specified tag from CHANGELOG.md.

    Matches headings like:
      ## [v1.0.4] - 2026-10-17
      ## [1.0.4] - 2026-10-17
      ## v1.0.4
    """
    if not changelog_path.exists():
        return None

    content = changelog_path.read_text(encoding="utf-8")
    clean_tag = tag.lstrip("v")
    pattern = rf"^##\s+\[?(?:v)?{re.escape(clean_tag)}\]?(?:\s+-\s+.*)?$"

    lines = content.splitlines()
    in_section = False
    extracted_lines: List[str] = []

    for line in lines:
        if re.match(pattern, line.strip(), re.IGNORECASE):
            in_section = True
            continue
        elif in_section:
            if line.startswith("## "):
                break
            extracted_lines.append(line)

    if not in_section:
        return None

    result = "\n".join(extracted_lines).strip()
    return strip_emojis(result) if result else None


def categorize_commits(commit_lines: List[str]) -> Dict[str, List[str]]:
    """Categorizes git commit messages into standard semantic groups."""
    categories: Dict[str, List[str]] = {
        "Features": [],
        "Bug Fixes": [],
        "Performance Improvements": [],
        "Maintenance & Documentation": [],
    }

    for raw_line in commit_lines:
        line = strip_emojis(raw_line.strip())
        if not line:
            continue

        lower = line.lower()
        if lower.startswith("feat:") or lower.startswith("feat(") or lower.startswith("feature:"):
            categories["Features"].append(line)
        elif lower.startswith("fix:") or lower.startswith("fix(") or lower.startswith("bug:"):
            categories["Bug Fixes"].append(line)
        elif lower.startswith("perf:") or lower.startswith("perf("):
            categories["Performance Improvements"].append(line)
        elif any(lower.startswith(p) for p in ["docs:", "docs(", "chore:", "chore(", "refactor:", "refactor(", "ci:", "ci(", "test:", "test("]):
            categories["Maintenance & Documentation"].append(line)
        else:
            categories["Maintenance & Documentation"].append(line)

    return categories


def get_previous_tag(current_tag: str) -> Optional[str]:
    """Finds the git tag immediately preceding current_tag."""
    try:
        cmd = ["git", "describe", "--tags", "--abbrev=0", f"{current_tag}^"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def generate_from_git_log(tag: str, repo: str) -> str:
    """Generates structured markdown release notes by inspecting git log."""
    prev_tag = get_previous_tag(tag)
    range_spec = f"{prev_tag}..{tag}" if prev_tag else tag

    try:
        cmd = ["git", "log", range_spec, '--pretty=format:%s (%h)']
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        commits = res.stdout.splitlines() if res.returncode == 0 else []
    except Exception:
        commits = []

    categorized = categorize_commits(commits)
    parts: List[str] = [f"## Speech-To-Text {tag}\n"]

    for group, items in categorized.items():
        if items:
            parts.append(f"### {group}")
            for it in items:
                parts.append(f"- {it}")
            parts.append("")

    if prev_tag:
        parts.append(f"**Full Changelog**: https://github.com/{repo}/compare/{prev_tag}...{tag}")
    else:
        parts.append(f"**Full Changelog**: https://github.com/{repo}/commits/{tag}")

    return "\n".join(parts).strip()


def build_release_notes(
    tag: str,
    changelog_path: Optional[Path] = None,
    sha256_path: Optional[Path] = None,
    sha256_setup_path: Optional[Path] = None,
    repo: str = "The0Sanity/Speech-To-Text",
) -> str:
    """Constructs the complete release notes body for GitHub Releases."""
    notes_body: Optional[str] = None
    if changelog_path and changelog_path.exists():
        notes_body = extract_from_changelog(changelog_path, tag)

    if not notes_body:
        notes_body = generate_from_git_log(tag, repo)

    # Clean any accidental emoji
    notes_body = strip_emojis(notes_body)

    if not notes_body.startswith(f"## Speech-To-Text {tag}") and not notes_body.startswith(f"## {tag}"):
        notes_body = f"## Speech-To-Text {tag}\n\n{notes_body}"

    sections: List[str] = [notes_body]

    # SHA256 Checksum block
    checksum_lines = []
    if sha256_path and sha256_path.exists():
        sha_val = sha256_path.read_text(encoding="utf-8").strip()
        if sha_val:
            checksum_lines.append(f"- `SpeechToText.exe` (Portable): `{sha_val.split()[0]}`")
    if sha256_setup_path and sha256_setup_path.exists():
        sha_setup_val = sha256_setup_path.read_text(encoding="utf-8").strip()
        if sha_setup_val:
            checksum_lines.append(f"- `SpeechToText-Setup.exe` (Installer): `{sha_setup_val.split()[0]}`")

    if checksum_lines:
        sections.append(
            "### Checksum Verification (SHA-256)\n"
            "Verify file integrity in PowerShell before running:\n\n"
            + "\n".join(checksum_lines)
            + "\n\nExample PowerShell verification:\n"
            + "```powershell\n"
            + "(Get-FileHash -Algorithm SHA256 .\\SpeechToText.exe).Hash\n"
            + "```"
        )

    # Windows SmartScreen Guidance
    sections.append(
        "### Windows Installation & SmartScreen Guidance\n"
        "- **Dual Packaging Formats Provided**:\n"
        "  - `SpeechToText.exe`: Standalone portable executable. Extract and run directly without installation.\n"
        "  - `SpeechToText-Setup.exe`: Inno Setup Windows installer with Start Menu and optional Desktop shortcuts.\n"
        '- If Windows SmartScreen displays "Windows protected your PC", click **More info** and select **Run anyway**.\n'
        "- Binaries are timestamped with Authenticode signatures for tamper detection."
    )

    # Prominent Visual Attribution & Licensing Notice
    sections.append(
        "### Licensing & Attribution Notice\n"
        "This project is open-source under the MIT License with Prominent Visual Attribution Requirement.\n"
        "Any derivative application or redistributable incorporating this software must visually display a clear, clickable link to https://github.com/The0Sanity/Speech-To-Text on its primary interface."
    )

    full_notes = "\n\n".join(sections)
    return strip_emojis(full_notes).strip()


def main():
    parser = argparse.ArgumentParser(description="Generate patch notes for GitHub Release.")
    parser.add_argument("--tag", required=True, help="Release tag (e.g. v1.0.6)")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to CHANGELOG.md")
    parser.add_argument("--sha256", default=None, help="Path to portable .sha256 file")
    parser.add_argument("--sha256-setup", default=None, help="Path to setup .sha256 file")
    parser.add_argument("--output", default=None, help="Output markdown file path")
    parser.add_argument("--repo", default="The0Sanity/Speech-To-Text", help="GitHub repo (owner/name)")

    args = parser.parse_args()

    cl_path = Path(args.changelog) if args.changelog else None
    sha_path = Path(args.sha256) if args.sha256 else None
    sha_setup_path = Path(args.sha256_setup) if args.sha256_setup else None

    notes = build_release_notes(
        tag=args.tag,
        changelog_path=cl_path,
        sha256_path=sha_path,
        sha256_setup_path=sha_setup_path,
        repo=args.repo,
    )

    if args.output:
        out_file = Path(args.output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(notes, encoding="utf-8")
        print(f"Release notes written to {out_file} ({len(notes)} bytes)")
    else:
        print(notes)


if __name__ == "__main__":
    main()
