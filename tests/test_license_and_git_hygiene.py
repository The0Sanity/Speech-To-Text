import os
import subprocess
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestLicenseAndGitHygiene(unittest.TestCase):
    def test_license_file_exists_and_is_mit(self):
        license_path = os.path.join(ROOT_DIR, "LICENSE")
        self.assertTrue(os.path.isfile(license_path), "LICENSE file must exist at repo root")

        with open(license_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("MIT License", content)
        self.assertIn("The0Sanity", content)
        self.assertIn("Permission is hereby granted, free of charge", content)

        # Check for zero emojis
        for char in content:
            self.assertLess(
                ord(char),
                0x1F000,
                f"Emoji or high-range unicode character detected in LICENSE: {char}",
            )

    def test_gitignore_contains_required_rules(self):
        gitignore_path = os.path.join(ROOT_DIR, ".gitignore")
        self.assertTrue(os.path.isfile(gitignore_path), ".gitignore file must exist at repo root")

        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

        required_patterns = ["temp/", "CLAUDE.md", "GEMINI.md"]
        for pattern in required_patterns:
            self.assertTrue(
                any(pattern in line for line in lines),
                f"Pattern '{pattern}' missing from .gitignore",
            )

    def test_unnecessary_files_not_tracked_in_git(self):
        try:
            res = subprocess.run(
                ["git", "ls-files"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=True,
            )
            tracked_files = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
        except Exception as e:
            self.skipTest(f"git command not available or failed: {e}")

        unwanted_tracked = [
            "CLAUDE.md",
            "GEMINI.md",
            "temp/.gitkeep",
        ]
        for unwanted in unwanted_tracked:
            self.assertNotIn(
                unwanted,
                tracked_files,
                f"Unwanted file '{unwanted}' must not be tracked in git index",
            )


if __name__ == "__main__":
    unittest.main()
