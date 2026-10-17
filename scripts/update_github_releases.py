#!/usr/bin/env python3
"""
Updates release notes for existing published GitHub releases one by one.
Reads curated release notes from CHANGELOG.md and updates GitHub via REST API.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_patch_notes import build_release_notes, strip_emojis


def get_github_token() -> Optional[str]:
    """Retrieves GitHub token from environment or Git Credential Manager."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token

    try:
        p = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, _ = p.communicate("protocol=https\nhost=github.com\n")
        creds = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        return creds.get("password")
    except Exception as e:
        print(f"Could not retrieve git credentials: {e}")
        return None


def fetch_all_releases(repo: str, token: Optional[str] = None) -> List[Dict]:
    """Fetches all releases from GitHub repository."""
    url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
    headers = {
        "User-Agent": "SesMetinPro-ReleaseManager",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_release_asset_text(asset_url: str, token: Optional[str] = None) -> Optional[str]:
    """Downloads text content of a release asset (e.g. .sha256)."""
    headers = {
        "User-Agent": "SesMetinPro-ReleaseManager",
        "Accept": "application/octet-stream",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(asset_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return None


def update_release_notes(
    repo: str,
    release_id: int,
    tag: str,
    body: str,
    token: str,
) -> bool:
    """Sends PATCH request to update a GitHub release body."""
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "SesMetinPro-ReleaseManager",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    payload = json.dumps({
        "body": body,
        "name": f"Speech-To-Text {tag}",
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                return True
            print(f"Update returned status: {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"HTTPError updating release {tag} (id {release_id}): {e.code} - {err_msg}")
        return False
    except Exception as e:
        print(f"Error updating release {tag} (id {release_id}): {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Update patch notes for existing GitHub releases.")
    parser.add_argument("--repo", default="The0Sanity/Speech-To-Text", help="GitHub repo (owner/name)")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to master CHANGELOG.md")
    parser.add_argument("--dry-run", action="store_true", help="Print updates without publishing to GitHub")
    parser.add_argument("--tags", nargs="*", default=None, help="Specific tags to update (default: all)")

    args = parser.parse_args()

    token = get_github_token()
    if not token and not args.dry_run:
        print("Error: GitHub token not found in environment or Git Credential Manager.")
        sys.exit(1)

    changelog_path = Path(args.changelog)
    if not changelog_path.exists():
        print(f"Error: {changelog_path} not found.")
        sys.exit(1)

    print(f"Fetching published releases for {args.repo}...")
    releases = fetch_all_releases(args.repo, token)
    print(f"Found {len(releases)} total releases on GitHub.\n")

    target_tags = set(args.tags) if args.tags else None

    # Sort releases oldest to newest or process one by one
    sorted_releases = sorted(releases, key=lambda r: r.get("published_at") or "")

    for r in sorted_releases:
        tag = r.get("tag_name", "")
        rel_id = r.get("id")

        if target_tags and tag not in target_tags:
            continue

        print(f"--------------------------------------------------")
        print(f"Processing Release: {tag} (ID: {rel_id})")

        # Check if release has a .sha256 asset
        sha_text = None
        for asset in r.get("assets", []):
            if asset.get("name", "").endswith(".sha256"):
                asset_url = asset.get("url")
                sha_text = fetch_release_asset_text(asset_url, token)
                break

        # If sha_text found, write to temporary file for generator
        sha_file = None
        if sha_text:
            sha_file = PROJECT_ROOT / "temp" / f"{tag}.sha256"
            sha_file.parent.mkdir(parents=True, exist_ok=True)
            sha_file.write_text(sha_text, encoding="utf-8")

        # Build comprehensive release notes
        notes = build_release_notes(
            tag=tag,
            changelog_path=changelog_path,
            sha256_path=sha_file,
            repo=args.repo,
        )

        print(f"Generated patch notes length: {len(notes)} chars")
        if args.dry_run:
            print(f"[DRY-RUN] Would update release {tag} with notes:\n")
            print(notes[:300] + ("\n...\n" if len(notes) > 300 else ""))
        else:
            success = update_release_notes(
                repo=args.repo,
                release_id=rel_id,
                tag=tag,
                body=notes,
                token=token,
            )
            if success:
                print(f"SUCCESS: Release {tag} (ID: {rel_id}) updated successfully.")
            else:
                print(f"FAILED: Could not update release {tag}.")

        print()

    print("All target releases processed.")


if __name__ == "__main__":
    main()
