#!/usr/bin/env python3
"""Build styled ASS and plain SRT captions for the Book I preview."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "captions" / "book-01-preview-cues-v4.json"
ASS_OUTPUT = ROOT / "captions" / "book-01-preview-v4.ass"
SRT_OUTPUT = ROOT / "captions" / "book-01-preview-v4.srt"


def ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def narration_text(text: str) -> str:
    """Render narration plainly; color no longer implies active-word timing."""
    return text.replace("\\n", "\\N")


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    cues = data["cues"]

    ass_header = """[Script Info]
Title: Odyssey Book I — Living Manuscript Preview
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Georgia,74,&H006AB3D7,&H006AB3D7,&HCC130D08,&H80000000,0,0,0,0,100,100,7,0,1,3,2,5,120,120,0,1
Style: Deck,Georgia,35,&H00C7DDE8,&H00C7DDE8,&HCC130D08,&H80000000,0,1,0,0,100,100,1,0,1,2.5,1,5,210,210,0,1
Style: Header,Georgia,23,&H005594B8,&H005594B8,&H80130D08,&H00000000,0,0,0,0,100,100,3,0,1,1.5,0,8,80,80,54,1
Style: Narration,Georgia,49,&H00D8E7EE,&H00D8E7EE,&HE0130D08,&H70000000,0,0,0,0,100,100,0.4,0,1,3,1,2,170,170,185,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    title = next(cue for cue in cues if cue.get("kind") == "title")
    deck = next(cue for cue in cues if cue.get("kind") == "deck")
    narration_start = next(cue["start"] for cue in cues if not cue.get("kind"))

    events = [
        f"Dialogue: 0,{ass_time(title['start'])},{ass_time(title['end'])},Title,,0,0,0,,"
        r"{\pos(960,445)\fad(600,500)\bord3\blur0.5}ODYSSEY — BOOK I",
        f"Dialogue: 0,{ass_time(deck['start'])},{ass_time(deck['end'])},Deck,,0,0,0,,"
        r"{\pos(960,565)\fad(600,500)}Athena comes to Ithaca;\NTelemachus resolves to seek his father.",
        f"Dialogue: 0,{ass_time(narration_start)},{ass_time(data['duration'])},Header,,0,0,0,,"
        r"{\fad(800,500)}HOMER’S ODYSSEY  ·  BOOK I",
    ]

    srt_blocks = []
    srt_index = 1
    for cue in cues:
        if cue.get("kind"):
            continue
        start = float(cue["start"])
        end = float(cue["end"])
        highlighted = narration_text(cue["text"])
        events.append(
            f"Dialogue: 1,{ass_time(start)},{ass_time(end)},Narration,,0,0,0,,"
            rf"{{\fad(60,120)}}{highlighted}"
        )
        srt_blocks.append(
            f"{srt_index}\n{srt_time(start)} --> {srt_time(end)}\n"
            f"{cue['text'].replace(chr(92) + 'n', chr(10))}\n"
        )
        srt_index += 1

    ASS_OUTPUT.write_text(ass_header + "\n".join(events) + "\n", encoding="utf-8-sig")
    SRT_OUTPUT.write_text("\n".join(srt_blocks), encoding="utf-8")
    print(f"Wrote {ASS_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {SRT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
