import io
import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from unittest.mock import MagicMock, patch

from tools.huggingface.upload_dataset import gather_dataset_records, build_dataset_cards
from tools.huggingface.launch_cloud_training import launch_job
from tools.model_training.train_v2_model import main as train_v2_main


class TestHuggingFaceCloudPipeline(unittest.TestCase):
    """Tests ensuring model training is offloaded to Hugging Face Cloud and local compute is guarded."""

    def test_01_local_training_guard_blocks_execution_without_flag(self):
        """Executing train_v2_model without --allow-local-compute must block local compute."""
        test_args = ["train_v2_model.py"]
        captured_out = io.StringIO()

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", captured_out):
                train_v2_main()

        output = captured_out.getvalue()
        self.assertIn("Hugging Face bulut GPU", output)
        self.assertIn("launch_cloud_training.py", output)

    def test_02_dataset_records_contain_synthetic_and_dialogue_turns(self):
        """gather_dataset_records must collect structured records with domain, voice, and split."""
        records = gather_dataset_records()
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)

        first = records[0]
        self.assertIn("text", first)
        self.assertIn("domain", first)
        self.assertIn("split", first)

    def test_03_dataset_cards_has_valid_frontmatter(self):
        """Dataset card must have valid YAML metadata and official attribution link."""
        card = build_dataset_cards()
        self.assertTrue(card.startswith("---"))
        self.assertIn("language:", card)
        self.assertIn("tr", card)
        self.assertIn("The0Sanity/Speech-To-Text", card)

    @patch("tools.huggingface.launch_cloud_training.check_auth")
    def test_04_launch_cloud_training_prints_hf_jobs_cli_invocation(self, mock_check_auth):
        """launch_job should construct compliant hf jobs uv run invocation."""
        mock_check_auth.return_value = "The0Sanity"
        captured_out = io.StringIO()

        with patch.dict("os.environ", {"HF_TOKEN": "mock_token"}):
            with patch("sys.stdout", captured_out):
                launch_job(flavor="a10g-large", timeout="2h")

        output = captured_out.getvalue()
        self.assertIn("hf jobs uv run --flavor a10g-large", output)
        self.assertIn("Zero local CPU/GPU cycles are used", output)
        self.assertIn("The0Sanity", output)


if __name__ == "__main__":
    unittest.main()
