import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import soundfile as sf
from src.transcriber import WhisperTranscriber

def verify_pipeline():
    audio_path = "temp/yt_2d716075.wav"
    audio_data, sr = sf.read(audio_path, dtype="float32")
    
    # Write a 60s snippet
    snippet_path = "temp/verify_60s.wav"
    sf.write(snippet_path, audio_data[:60 * sr], sr)
    
    print("--- 1. Testing WhisperTranscriber('small') through full pipeline ---", flush=True)
    t_small = WhisperTranscriber(model_size="small", cpu_threads=4)
    res_small = t_small.transcribe(snippet_path, apply_postprocessing=True)
    print(f"Segment count: {len(res_small)}", flush=True)
    for r in res_small:
        print(f"[{r['start']:5.1f}s -> {r['end']:5.1f}s]: {r['text']}", flush=True)
        
    full_text = " ".join(r["text"] for r in res_small)
    print("\nFULL EXTRACTED TEXT (small):", full_text, flush=True)
    assert len(res_small) > 0, "Pipeline produced empty segments!"
    assert "patates" in full_text.lower(), "Expected lyrics not found!"

    print("\n--- 2. Testing WhisperTranscriber('sesmetin-v2-tiny') through full pipeline ---", flush=True)
    t_tiny = WhisperTranscriber(model_size="sesmetin-v2-tiny", cpu_threads=4)
    res_tiny = t_tiny.transcribe(snippet_path, apply_postprocessing=True)
    print(f"Tiny Segment count: {len(res_tiny)}", flush=True)
    for r in res_tiny:
        print(f"[{r['start']:5.1f}s -> {r['end']:5.1f}s]: {r['text']}", flush=True)
    tiny_full_text = " ".join(r["text"] for r in res_tiny)
    print("\nFULL EXTRACTED TEXT (tiny):", tiny_full_text, flush=True)
    assert len(res_tiny) > 0, "Tiny pipeline produced empty segments!"

    print("\nPIPELINE VERIFICATION SUCCESSFUL FOR BOTH MODELS!", flush=True)

if __name__ == "__main__":
    verify_pipeline()
