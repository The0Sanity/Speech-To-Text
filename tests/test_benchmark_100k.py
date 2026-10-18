"""Unit tests for the 100k streaming benchmark harness in SesMetin Pro.

Verifies synthetic test generation, parallel batch evaluation, Word Error Rate (WER)
computation, and statistical reporting.
"""

import unittest
from tools.benchmarks.benchmark_100k_tests import (
    SyntheticTestStreamer,
    BenchmarkRunner,
    BenchmarkConfig,
    calculate_wer,
    calculate_cer
)


class TestBenchmark100k(unittest.TestCase):
    """Test suite for the 100,000 MP3 streaming benchmark framework."""

    def test_wer_and_cer_calculation(self):
        """Verify standard WER and CER calculations."""
        ref = "ses metin pro yuksek performansli model"
        hyp = "ses metin pro yuksek performansli model"
        self.assertEqual(calculate_wer(ref, hyp), 0.0)
        self.assertEqual(calculate_cer(ref, hyp), 0.0)

        # 1 error in 5 words -> WER = 0.20
        ref_5 = "ses metin yuksek performansli model"
        hyp_err = "ses metin yuksek basarili model"
        self.assertAlmostEqual(calculate_wer(ref_5, hyp_err), 0.20, places=2)

    def test_synthetic_streamer_generation(self):
        """Verify the streamer yields audio-text pairs with correct metadata."""
        streamer = SyntheticTestStreamer(domains=["conversational", "itn", "technical"])
        samples = list(streamer.generate_stream(batch_size=10, max_samples=25))

        self.assertEqual(len(samples), 25)
        for s in samples:
            self.assertIn("audio", s)
            self.assertIn("reference_text", s)
            self.assertIn("domain", s)
            self.assertGreater(len(s["reference_text"]), 0)
            self.assertEqual(s["audio"].ndim, 1)

    def test_benchmark_runner_small_run(self):
        """Verify BenchmarkRunner executes in fast validation mode."""
        config = BenchmarkConfig(
            total_tests=50,
            batch_size=10,
            max_workers=2,
            target_wer_percentage=0.1
        )
        runner = BenchmarkRunner(config)
        report = runner.run_benchmark(progress_callback=None)

        self.assertIn("total_tests", report)
        self.assertEqual(report["total_tests"], 50)
        self.assertIn("mean_wer", report)
        self.assertIn("mean_cer", report)
        self.assertIn("itn_accuracy", report)
        self.assertIn("samples_per_second", report)
        self.assertLessEqual(report["mean_wer"], 0.05)

    def test_million_hour_simulation_benchmark(self):
        """Verify the 1,000,000 hour simulation benchmark executes and achieves < 0.1% WER."""
        config = BenchmarkConfig(
            total_tests=100,
            batch_size=20,
            max_workers=2,
            target_wer_percentage=0.1
        )
        runner = BenchmarkRunner(config)
        report = runner.run_million_hour_simulation_benchmark(simulated_hours=1000000.0, sample_size=100)
        self.assertEqual(report["simulated_hours"], 1000000.0)
        self.assertLessEqual(report["mean_wer_percentage"], 0.1)
        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
