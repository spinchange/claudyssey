#!/usr/bin/env python3
"""Transcribe Book I narration with word-level timestamps using faster-whisper."""

from __future__ import annotations

import json
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio-chunks" / "book-01" / "chunk-001.mp3"
MODEL_ROOT = ROOT / "models" / "faster-whisper-tiny.en"
OUTPUT = ROOT / "captions" / "book-01-preview-words.json"


def main() -> None:
    model = WhisperModel(
        "tiny.en",
        device="cpu",
        compute_type="int8",
        download_root=str(MODEL_ROOT),
    )
    segments, info = model.transcribe(
        str(AUDIO),
        language="en",
        beam_size=5,
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=True,
    )

    words = []
    transcript = []
    for segment in segments:
        transcript.append(segment.text.strip())
        for word in segment.words or []:
            words.append(
                {
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "probability": round(word.probability, 5),
                }
            )

    payload = {
        "audio": str(AUDIO.relative_to(ROOT)),
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "transcript": " ".join(transcript),
        "words": words,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(words)} timed words")


if __name__ == "__main__":
    main()
