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
            "settings.json",
            "config.json",
        ]
        for unwanted in unwanted_tracked:
            self.assertNotIn(
                unwanted,
                tracked_files,
                f"Unwanted file '{unwanted}' must not be tracked in git index",
            )

    def test_license_contains_prominent_visual_attribution_clause(self):
        license_path = os.path.join(ROOT_DIR, "LICENSE")
        with open(license_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Visual Attribution Requirement", content)
        self.assertIn("https://github.com/The0Sanity/Speech-To-Text", content)
        self.assertIn("prominent", content.lower())
        self.assertTrue(
            "hiding" in content.lower() or "obscuring" in content.lower(),
            "License must explicitly prohibit hiding or obscuring visual attribution",
        )

    def test_readme_documents_visual_attribution(self):
        readme_path = os.path.join(ROOT_DIR, "README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("https://github.com/The0Sanity/Speech-To-Text", content)
        self.assertTrue(
            "görsel" in content.lower() or "visual" in content.lower() or "atf" in content.lower() or "attribution" in content.lower(),
            "README.md must document visual attribution requirement",
        )

    def test_release_ci_workflow_and_spec_exist(self):
        workflow_path = os.path.join(ROOT_DIR, ".github", "workflows", "release.yml")
        self.assertTrue(os.path.isfile(workflow_path), ".github/workflows/release.yml must exist")

        spec_path = os.path.join(ROOT_DIR, "SpeechToText.spec")
        self.assertTrue(os.path.isfile(spec_path), "SpeechToText.spec must exist for PyInstaller build")

        build_bat = os.path.join(ROOT_DIR, "scripts", "build_exe.bat")
        self.assertTrue(os.path.isfile(build_bat), "scripts/build_exe.bat must exist")

    def test_app_header_contains_prominent_repo_attribution(self):
        app_path = os.path.join(ROOT_DIR, "src", "ui", "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("https://github.com/The0Sanity/Speech-To-Text", content)
        self.assertIn("The0Sanity/Speech-To-Text", content)


if __name__ == "__main__":
    unittest.main()

