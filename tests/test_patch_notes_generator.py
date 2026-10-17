"""
Unit tests for the automated patch notes generation script.
Stage 3: Test-First discipline under Superpowers Framework.
"""

import os
import sys
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.generate_patch_notes import (
    build_release_notes,
    categorize_commits,
    extract_from_changelog,
    has_emojis,
)


class TestPatchNotesGenerator(unittest.TestCase):
    """Test suite for patch notes generation and changelog extraction."""

    def test_extract_from_changelog_found(self):
        """Extracts release notes block for a specific version tag from CHANGELOG.md."""
        sample_changelog = """# Changelog

## [v1.0.4] - 2026-10-17
### Added
- Bundled Flet material icons.

### Fixed
- Fixed crash on fresh installs.

## [v1.0.3] - 2026-10-17
### Security
- Authenticode signing.
"""
        with NamedTemporaryFile("w+", delete=False, encoding="utf-8", suffix=".md") as tmp:
            tmp.write(sample_changelog)
            tmp_path = Path(tmp.name)

        try:
            notes = extract_from_changelog(tmp_path, "v1.0.4")
            self.assertIsNotNone(notes)
            self.assertIn("Bundled Flet material icons", notes)
            self.assertIn("Fixed crash on fresh installs", notes)
            self.assertNotIn("Authenticode signing", notes)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_extract_from_changelog_not_found(self):
        """Returns None if the specified version tag is not in CHANGELOG.md."""
        sample_changelog = """# Changelog
## [v1.0.1] - 2026-10-17
- Some notes.
"""
        with NamedTemporaryFile("w+", delete=False, encoding="utf-8", suffix=".md") as tmp:
            tmp.write(sample_changelog)
            tmp_path = Path(tmp.name)

        try:
            notes = extract_from_changelog(tmp_path, "v9.9.9")
            self.assertIsNone(notes)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_categorize_commits(self):
        """Categorizes raw commit messages into structured sections."""
        commits = [
            "feat(updater): implement smooth progress bar (a507189)",
            "fix(packaging): bundle flet icons (b1d3d5f)",
            "perf(diarization): optimize pitch calculation (9ce7bc4)",
            "docs: rewrite readme (1ea1a4f)",
            "chore: update dependencies (abcdef1)",
        ]
        categories = categorize_commits(commits)
        self.assertIn("Features", categories)
        self.assertIn("Bug Fixes", categories)
        self.assertIn("Performance Improvements", categories)
        self.assertIn("Maintenance & Documentation", categories)

        self.assertEqual(len(categories["Features"]), 1)
        self.assertEqual(len(categories["Bug Fixes"]), 1)
        self.assertEqual(len(categories["Performance Improvements"]), 1)
        self.assertEqual(len(categories["Maintenance & Documentation"]), 2)

    def test_build_release_notes_includes_checksum_and_attribution(self):
        """Builds release notes containing sha256 checksum and attribution notice."""
        with TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            cl_path = dir_path / "CHANGELOG.md"
            cl_path.write_text("## [v1.0.6] - 2026-10-17\n- Enhanced smooth updater.\n", encoding="utf-8")

            sha_path = dir_path / "SpeechToText.exe.sha256"
            sha_path.write_text("abcdef1234567890abcdef1234567890\n", encoding="utf-8")

            notes = build_release_notes(
                tag="v1.0.6",
                changelog_path=cl_path,
                sha256_path=sha_path,
                repo="The0Sanity/Speech-To-Text",
            )

            self.assertIn("v1.0.6", notes)
            self.assertIn("Enhanced smooth updater", notes)
            self.assertIn("abcdef1234567890abcdef1234567890", notes)
            self.assertIn("https://github.com/The0Sanity/Speech-To-Text", notes)
            self.assertFalse(has_emojis(notes))


if __name__ == "__main__":
    unittest.main()
