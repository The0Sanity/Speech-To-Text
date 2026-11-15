import re
import unittest
from pathlib import Path


class TestReadmeAndRoadmap(unittest.TestCase):
    """Test suite ensuring documentation quality, language switching, roadmap completeness, and zero emojis."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.readme_tr = self.root_dir / "README.md"
        self.readme_en = self.root_dir / "README.en.md"

    def test_both_readme_files_exist(self):
        """Verify that both Turkish (README.md) and English (README.en.md) documents exist."""
        self.assertTrue(self.readme_tr.exists(), "README.md must exist")
        self.assertTrue(self.readme_en.exists(), "README.en.md must exist")

    def test_language_navigation_bar_present(self):
        """Verify that language switcher links exist at the top of both READMEs."""
        content_tr = self.readme_tr.read_text(encoding="utf-8")
        content_en = self.readme_en.read_text(encoding="utf-8")

        for content, name in [(content_tr, "README.md"), (content_en, "README.en.md")]:
            self.assertIn("README.md", content, f"{name} must contain link to README.md")
            self.assertIn("README.en.md", content, f"{name} must contain link to README.en.md")
            self.assertIn("Türkçe", content, f"{name} must contain 'Türkçe' language label")
            self.assertIn("English", content, f"{name} must contain 'English' language label")

    def test_readmes_point_to_measured_results_and_the_plan(self):
        """Both READMEs name the current and the next version and link the documents behind their claims."""
        for path, name in [(self.readme_tr, "README.md"), (self.readme_en, "README.en.md")]:
            content = path.read_text(encoding="utf-8")
            for needed in ("v1.1.6", "v2.0.0", "docs/BENCHMARKS.md", "docs/PARITY.md", "- [x]", "- [ ]"):
                self.assertIn(needed, content, f"{name} must contain {needed}")
            for doc in ("docs/BENCHMARKS.md", "docs/PARITY.md", "docs/adr/0001-rewrite-app-in-rust.md"):
                self.assertTrue((self.root_dir / doc).is_file(), f"{doc} is linked from {name} and must exist")

    def test_readmes_make_no_unmeasured_accuracy_or_signing_claims(self):
        """Claims that were in the README without evidence must not come back."""
        for path in (self.readme_tr, self.readme_en):
            content = path.read_text(encoding="utf-8")
            for banned in ("Authenticode", "0.000%", "1,000,000", "99.79", "%4.2"):
                self.assertNotIn(banned, content, f"{path.name} contains unsupported claim: {banned}")

    def test_no_low_level_test_commands(self):
        """Verify user-facing README does not clutter with unit test discovery commands."""
        content = self.readme_tr.read_text(encoding="utf-8")
        self.assertNotIn("unittest discover", content, "User-facing README should not list internal test commands")

    def test_zero_emojis_in_readmes(self):
        """Verify strict zero-emoji policy across all markdown documentation."""
        emoji_pattern = re.compile(
            r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
        )
        for path in [self.readme_tr, self.readme_en]:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                matches = emoji_pattern.findall(text)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Found emojis in {path.name}: {matches[:5]}. Strict zero-emoji policy enforced.",
                )

    def test_visual_attribution_preserved(self):
        """Verify prominent visual attribution requirement is clearly maintained."""
        for path in [self.readme_tr, self.readme_en]:
            if path.exists():
                content = path.read_text(encoding="utf-8")
                self.assertIn(
                    "https://github.com/The0Sanity/Speech-To-Text",
                    content,
                    f"{path.name} must prominently reference repository URL for visual attribution",
                )


if __name__ == "__main__":
    unittest.main()
