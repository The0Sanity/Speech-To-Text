"""Test suite for WhisperTranscriber anti-loop protection and trailing repetition cleaning."""

import pytest
from src.transcriber import (
    clean_trailing_repetitions,
    should_filter_segment,
    is_repetition_loop,
    get_adaptive_vad_parameters,
)


def test_clean_trailing_repetitions_preserves_head():
    """Ensure trailing loops like 'sekiz patates sekiz patates...' are truncated without dropping valid content."""
    # 5 repeats of 'sekiz patates' at the end of a valid sentence
    text = "Bir patates patates iki patates sekiz patates sekiz patates sekiz patates sekiz patates sekiz patates"
    cleaned = clean_trailing_repetitions(text, max_repeats=2)
    
    assert "Bir patates patates iki patates" in cleaned, "Head content must be preserved!"
    # Should contain at most 2 repeats of 'sekiz patates'
    count = cleaned.lower().count("sekiz patates")
    assert count <= 2, f"Expected at most 2 trailing repeats, got {count} in: {cleaned}"


def test_clean_trailing_single_word_loops():
    """Ensure trailing single word repetitions like 'patates patates patates patates' are clamped."""
    text = "On patates patates patates patates patates patates patates patates"
    cleaned = clean_trailing_repetitions(text, max_repeats=2)
    assert cleaned.startswith("On patates")
    words = cleaned.split()
    assert words.count("patates") <= 3  # Initial + max 2 repeats


def test_adaptive_vad_low_threshold_on_music():
    """Adaptive VAD should provide relaxed threshold for singing/music."""
    params = get_adaptive_vad_parameters(is_music=True)
    assert params["threshold"] <= 0.20, f"Expected threshold <= 0.20 for music, got {params['threshold']}"
    assert params["min_silence_duration_ms"] >= 600, "Expected longer min_silence to prevent slicing lyrics"


def test_should_filter_segment_does_not_drop_normal_singing():
    """A segment with rich lyrics should not be completely dropped even if it has slight repetition."""
    valid_lyrics = "Bir patates, patates, iki patates, pa patates, üç patates, pa pa patates, dört patates"
    # Even if compression ratio is moderate, it should not be discarded
    dropped = should_filter_segment(avg_logprob=-0.45, no_speech_prob=0.05, text=valid_lyrics)
    assert not dropped, "Valid song lyrics must not be dropped by should_filter_segment!"
