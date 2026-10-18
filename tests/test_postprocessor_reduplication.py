"""Test suite for Turkish reduplication preservation and non-destructive hallucination handling."""

import pytest
from src.text_postprocessor import (
    postprocess_segments,
    _is_hallucination,
    _remove_repeated_phrases,
)


def test_turkish_reduplications_preserved():
    """Turkish reduplications (ikilemeler) like 'pisi pisi' must not be collapsed into 'pisi'."""
    text = "Gel pisi pisi buraya gel"
    cleaned = _remove_repeated_phrases(text)
    assert "pisi pisi" in cleaned, f"Expected 'pisi pisi' preserved, got: {cleaned}"

    text_kucu = "Kuçu kuçu kuçu kuçu gel"
    cleaned_kucu = _remove_repeated_phrases(text_kucu)
    assert "kuçu kuçu" in cleaned_kucu.lower(), f"Expected 'kuçu kuçu' preserved, got: {cleaned_kucu}"

    text_yavas = "Yavaş yavaş ilerliyoruz"
    cleaned_yavas = _remove_repeated_phrases(text_yavas)
    assert "Yavaş yavaş" in cleaned_yavas or "yavaş yavaş" in cleaned_yavas.lower()


def test_nursery_rhyme_phrases_not_dropped_as_hallucinations():
    """Rhythmic rhyming phrases like 'Domates domates.' should not be treated as hallucinations."""
    sample_text = "Domates domates. Domates domates."
    # _is_hallucination must return False for meaningful Turkish lyrics
    assert not _is_hallucination(sample_text), f"'{sample_text}' was incorrectly flagged as hallucination"

    pisi_text = "Gel pisi pisi pisi pisi pisi gel."
    assert not _is_hallucination(pisi_text), f"'{pisi_text}' was incorrectly flagged as hallucination"


def test_destructive_segment_filtering_disabled_for_nursery_rhymes():
    """Verify postprocess_segments preserves legitimate repetitive lyrics."""
    segments = [
        {"id": 1, "start": 0.0, "end": 5.0, "text": "Bir patates patates."},
        {"id": 2, "start": 5.5, "end": 10.0, "text": "Domates domates. Domates domates."},
        {"id": 3, "start": 10.5, "end": 15.0, "text": "Haydi sen de katıl benimle pisi pisi görmeye."},
        {"id": 4, "start": 15.5, "end": 20.0, "text": "Haydi sen de katıl benimle pisi pisi görmeye."},
    ]

    result = postprocess_segments(segments, remove_hallucinations=True, remove_repeated_phrases=True)
    assert len(result) >= 3, f"Expected at least 3 segments preserved, got {len(result)}"
    texts = " ".join(s["text"] for s in result)
    assert "patates" in texts
    assert "domates" in texts.lower()
    assert "pisi pisi" in texts


def test_junk_hallucinations_still_filtered():
    """Verify actual music tags or YouTube overlays are still removed."""
    assert _is_hallucination("[müzik]")
    assert _is_hallucination("[music]")
    assert _is_hallucination("abone olun")
    assert _is_hallucination("  ... ???  ")
