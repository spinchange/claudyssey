#!/usr/bin/env python3
"""Align Version 3 caption clauses to faster-whisper word timestamps."""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CUES = ROOT / "captions" / "book-01-preview-cues-v3.json"
WORD_TIMES = ROOT / "captions" / "book-01-preview-words.json"
OUTPUT_CUES = ROOT / "captions" / "book-01-preview-cues-v4.json"
REPORT = ROOT / "captions" / "book-01-preview-alignment-v4.txt"
VISUAL_LEAD = 0.16


def tokens(text: str) -> list[str]:
    text = text.replace("\\n", " ").replace("’", "'").lower()
    return [re.sub(r"[^a-z0-9']", "", token) for token in re.findall(r"[a-z0-9']+", text)]


def main() -> None:
    cue_data = json.loads(SOURCE_CUES.read_text(encoding="utf-8"))
    word_data = json.loads(WORD_TIMES.read_text(encoding="utf-8"))
    title_cues = [cue.copy() for cue in cue_data["cues"] if cue.get("kind")]
    narration_cues = [cue.copy() for cue in cue_data["cues"] if not cue.get("kind")]

    source_words: list[str] = []
    cue_ranges: list[tuple[int, int]] = []
    for cue in narration_cues:
        start = len(source_words)
        source_words.extend(tokens(cue["text"]))
        cue_ranges.append((start, len(source_words)))

    recognized = word_data["words"]
    recognized_words = [tokens(word["word"])[0] if tokens(word["word"]) else "" for word in recognized]
    matcher = difflib.SequenceMatcher(None, source_words, recognized_words, autojunk=False)

    source_to_recognized: dict[int, int] = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            source_to_recognized[block.a + offset] = block.b + offset

    anchors: list[tuple[float, int, str]] = []
    for cue_index, (start, end) in enumerate(cue_ranges):
        candidates = [
            (source_index, source_to_recognized[source_index])
            for source_index in range(start, end)
            if source_index in source_to_recognized
        ]
        if not candidates:
            raise RuntimeError(f"No word-level anchor found for cue {cue_index + 1}: {narration_cues[cue_index]['text']}")
        source_index, recognized_index = candidates[0]
        word = recognized[recognized_index]
        anchor = max(0.0, float(word["start"]) - VISUAL_LEAD)
        anchors.append((anchor, recognized_index, word["word"]))

    # Keep every cue visible until the next precisely anchored clause begins.
    for index, cue in enumerate(narration_cues):
        cue["start"] = round(anchors[index][0], 3)
        if index + 1 < len(narration_cues):
            cue["end"] = round(anchors[index + 1][0], 3)
        else:
            _, final_range_end = cue_ranges[index]
            final_matches = [
                source_to_recognized[source_index]
                for source_index in range(cue_ranges[index][0], final_range_end)
                if source_index in source_to_recognized
            ]
            final_end = float(recognized[max(final_matches)]["end"]) + 0.25
            cue["end"] = round(final_end, 3)

    first_narration_start = narration_cues[0]["start"]
    for cue in title_cues:
        cue["start"] = 0.0
        cue["end"] = first_narration_start

    duration = narration_cues[-1]["end"]
    payload = {"duration": duration, "cues": title_cues + narration_cues}
    OUTPUT_CUES.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    matching_source_words = len(source_to_recognized)
    lines = [
        "Odyssey Book I preview — Version 4 word alignment",
        f"Matched source words: {matching_source_words}/{len(source_words)} "
        f"({matching_source_words / len(source_words):.1%})",
        f"Visual lead: {VISUAL_LEAD:.2f}s",
        "",
        "Cue | V3 start | V4 start | Delta | Recognized anchor | Caption",
    ]
    for index, (old_cue, new_cue, anchor) in enumerate(
        zip(
            [cue for cue in cue_data["cues"] if not cue.get("kind")],
            narration_cues,
            anchors,
        ),
        start=1,
    ):
        delta = new_cue["start"] - float(old_cue["start"])
        caption = new_cue["text"].replace("\\n", " / ")
        lines.append(
            f"{index:>3} | {float(old_cue['start']):>8.3f} | {new_cue['start']:>8.3f} | "
            f"{delta:>+6.3f} | {anchor[2]:<18} | {caption}"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT_CUES.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(lines[1])


if __name__ == "__main__":
    main()
