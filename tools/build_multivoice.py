"""Build a multi-voice OpenAI TTS audiobook from the Odyssey Markdown.

Non-destructive companion to build_audiobook.py: reads ./audiobook-source,
writes only under ./audiobook-multivoice. The single-voice pipeline and its
finished audiobook-build output are never touched.

Stages:

1. tag        Segment cleaned text by speaker (quote-state machine plus
              formula-based attribution) and write per-book segment JSON
              and a human-readable review file.
2. prepare    Turn segments into voice-assigned, API-sized chunks and a
              manifest, using the casting table.
3. synthesize Generate one audio file per chunk, each with its cast voice.
4. concat     Join chunks into per-book files with ffmpeg.

Attribution that cannot be resolved is marked UNKNOWN in the review file;
fix those in overrides.json (speech ordinal -> speaker) and rerun tag.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_audiobook import (  # noqa: E402
    clean_markdown,
    speech_request,
    split_long_text,
    load_pronunciations,
    build_replacement_regex,
    replace_names
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = ROOT / "audiobook-source"
DEFAULT_BUILD_DIR = ROOT / "audiobook-multivoice"

DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_FORMAT = "mp3"
DEFAULT_MAX_CHARS = 3800

DEFAULT_PRON_PATH = ROOT / "index" / "pronunciations.tsv"
DEFAULT_PRONUNCIATIONS_FILE = str(DEFAULT_PRON_PATH) if DEFAULT_PRON_PATH.exists() else None
LOOKBACK_LINES = 4

# Speaker roster: canonical name -> alias patterns matched in narration
# intro lines. Epithets are included because Homeric intro formulas often
# carry the epithet rather than (or before) the name.
ROSTER: dict[str, list[str]] = {
    "Zeus": [r"\bZeus\b", r"father of men and gods", r"\bcloud-gatherer\b",
             r"son of Cronos"],
    "Athena": [r"\bAthena\b", r"\bgray-eyed\b", r"\bPallas\b"],
    "Telemachus": [r"\bTelemachus\b"],
    "Odysseus": [r"\bOdysseus\b", r"\bmuch-enduring\b", r"\bresourceful\b",
                 r"man of many turnings"],
    "Penelope": [r"\bPenelope\b", r"daughter of Icarius"],
    "Eurycleia": [r"\bEurycleia\b"],
    "Antinous": [r"\bAntinous\b"],
    "Eurymachus": [r"\bEurymachus\b"],
    "Nestor": [r"\bNestor\b"],
    "Menelaus": [r"\bMenelaus\b"],
    "Helen": [r"\bHelen\b"],
    "Calypso": [r"\bCalypso\b"],
    "Circe": [r"\bCirce\b"],
    "Alcinous": [r"\bAlcinous\b"],
    "Arete": [r"\bArete\b"],
    "Nausicaa": [r"\bNausicaa\b"],
    "Eumaeus": [r"\bEumaeus\b", r"\bswineherd\b"],
    "Laertes": [r"\bLaertes\b"],
    "Hermes": [r"\bHermes\b", r"slayer of Argus"],
    "Poseidon": [r"\bPoseidon\b", r"\bearth-shaker\b"],
    "Polyphemus": [r"\bPolyphemus\b", r"\bCyclops\b"],
    "Proteus": [r"\bProteus\b", r"old man of the sea"],
    "Eidothea": [r"\bEidothea\b"],
    "Mentor": [r"\bMentor\b"],
    "Theoclymenus": [r"\bTheoclymenus\b"],
    "Amphinomus": [r"\bAmphinomus\b"],
    "Melanthius": [r"\bMelanthius\b"],
    "Philoetius": [r"\bPhiloetius\b", r"\bcowherd\b"],
    "Agamemnon": [r"\bAgamemnon\b", r"son of Atreus"],
    "Achilles": [r"\bAchilles\b"],
    "Tiresias": [r"\bTiresias\b"],
    "Anticleia": [r"\bAnticleia\b"],
    "Ino": [r"\bIno\b", r"\bLeucothea\b"],
    "Aeolus": [r"\bAeolus\b"],
    "Demodocus": [r"\bDemodocus\b"],
    "Phemius": [r"\bPhemius\b"],
    "Medon": [r"\bMedon\b"],
    "Halitherses": [r"\bHalitherses\b"],
    "Aegyptius": [r"\bAegyptius\b"],
    "Peisistratus": [r"\bPeisistratus\b"],
    "Melantho": [r"\bMelantho\b"],
    "Ctesippus": [r"\bCtesippus\b"],
    "Agelaus": [r"\bAgelaus\b"],
    "Leocritus": [r"\bLeocritus\b"],
    "Leodes": [r"\bLeodes\b"],
    "Amphimedon": [r"\bAmphimedon\b"],
    "Dolius": [r"\bDolius\b"],
    "Elpenor": [r"\bElpenor\b"],
    "Heracles": [r"\bHeracles\b"],
}

FEMALE = {"Athena", "Penelope", "Eurycleia", "Helen", "Calypso", "Circe",
          "Arete", "Nausicaa", "Anticleia", "Ino", "Eidothea", "Melantho"}

# Names appearing directly after these verbs are addressees, not speakers.
ADDRESSEE_RE = re.compile(
    r"(?:answered|addressed|spoke to|said to|called to)\s+"
    r"(?:the\s+|noble\s+|godlike\s+|young\s+|old\s+)?(\w+)")

DEFAULT_CASTING = {
    "narrator": "fable",
    "Odysseus": "onyx",
    "Telemachus": "echo",
    "Zeus": "ballad",
    "Athena": "nova",
    "Penelope": "shimmer",
    "_default_male": "ash",
    "_default_female": "coral",
}

NARRATOR_INSTRUCTIONS = (
    "Read as a clear, measured, single-narrator literary audiobook. "
    "This is third-person narration between speeches."
)


# Extra delivery guidance for specific speakers, appended to the base
# character instructions.
SPEAKER_NOTES = {
    "Zeus": "Speak low, slow, and imposing: the father of gods and men, "
            "with effortless authority and no urgency.",
    "Athena (as Mentes)": "This is the goddess Athena disguised as Mentes, "
            "a seasoned seafaring chieftain. Speak entirely as a composed, "
            "worldly older man; nothing should betray the disguise.",
}


def character_instructions(name: str) -> str:
    base = (
        f"You are voicing the direct speech of {name} in a literary "
        f"audiobook of Homer's Odyssey. Deliver it as natural spoken "
        f"dialogue, measured and clear, without theatrical excess."
    )
    note = SPEAKER_NOTES.get(name)
    return f"{base} {note}" if note else base


def book_ids(source_dir: Path, selected: list[str] | None) -> list[str]:
    ids = [p.stem for p in sorted(source_dir.glob("book-*.md"))]
    if selected:
        missing = set(selected) - set(ids)
        if missing:
            raise SystemExit(f"Unknown book ids: {sorted(missing)}")
        return [b for b in ids if b in set(selected)]
    return ids


def attribute(lines: list[str], open_index: int, speech_lines: set[int]) -> str:
    """Name the speaker of the speech opening at lines[open_index]."""
    candidates: list[str] = []
    scanned = 0
    for j in range(open_index - 1, -1, -1):
        if scanned >= LOOKBACK_LINES:
            break
        if j in speech_lines:
            break
        line = lines[j].strip()
        if not line:
            continue
        scanned += 1
        addressees = {m.group(1) for m in ADDRESSEE_RE.finditer(line)}
        matches: list[tuple[int, str]] = []
        for name, patterns in ROSTER.items():
            for pattern in patterns:
                for m in re.finditer(pattern, line):
                    matched_word = line[m.start():m.end()].split()[-1]
                    if matched_word in addressees:
                        continue
                    matches.append((m.start(), name))
        if matches:
            matches.sort()
            candidates.append(matches[-1][1])
            break
    return candidates[0] if candidates else "UNKNOWN"


def segment_book(cleaned: str, overrides: dict[str, str]) -> list[dict]:
    """Split cleaned text into ordered {speaker, text} segments.

    All double quotes in this corpus sit at line start or line end (verified
    across all 24 books), so speech state is tracked per line: a line starting
    with '\"' opens a speech, a line ending with '\"' closes it.
    """
    lines = cleaned.splitlines()
    segments: list[dict] = []
    speech_lines: set[int] = set()
    current: list[str] = []
    speaker = "narrator"
    speech_ordinal = 0

    def flush() -> None:
        nonlocal current
        text = "\n".join(current).strip()
        if text:
            segments.append({"speaker": speaker, "text": text})
        current = []

    in_speech = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_speech and stripped.startswith('"'):
            flush()
            speech_ordinal += 1
            speaker = attribute(lines, i, speech_lines)
            speaker = overrides.get(str(speech_ordinal), speaker)
            in_speech = True
        if in_speech:
            speech_lines.add(i)
            current.append(line)
            if stripped.endswith('"') and len(stripped) > 1:
                flush()
                speaker = "narrator"
                in_speech = False
        else:
            current.append(line)
    flush()

    ordinal = 0
    for seg in segments:
        if seg["speaker"] != "narrator":
            ordinal += 1
            seg["ordinal"] = ordinal
    return segments


def cmd_tag(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir)
    build_dir = Path(args.build_dir)
    seg_dir = build_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)

    overrides_path = build_dir / "overrides.json"
    overrides_all: dict[str, dict[str, str]] = {}
    if overrides_path.exists():
        overrides_all = json.loads(overrides_path.read_text(encoding="utf-8"))

    review_lines: list[str] = []
    unknown_total = 0
    for book_id in book_ids(source_dir, args.books):
        text = (source_dir / f"{book_id}.md").read_text(encoding="utf-8")
        segments = segment_book(clean_markdown(text), overrides_all.get(book_id, {}))
        (seg_dir / f"{book_id}.json").write_text(
            json.dumps(segments, indent=2, ensure_ascii=False),
            encoding="utf-8", newline="\n")

        speeches = [s for s in segments if s["speaker"] != "narrator"]
        unknown = [s for s in speeches if s["speaker"] == "UNKNOWN"]
        unknown_total += len(unknown)
        review_lines.append(f"## {book_id}: {len(speeches)} speeches, "
                            f"{len(unknown)} unattributed")
        for s in speeches:
            first = s["text"].splitlines()[0]
            flag = "  <-- FIX" if s["speaker"] == "UNKNOWN" else ""
            review_lines.append(f"  [{s['ordinal']:3d}] {s['speaker']:<12} {first[:70]}{flag}")
        review_lines.append("")
        print(f"{book_id}: {len(segments)} segments, {len(speeches)} speeches, "
              f"{len(unknown)} unattributed")

    review_path = build_dir / "attribution-review.txt"
    review_path.write_text("\n".join(review_lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\nReview file: {review_path}")
    if unknown_total:
        print(f"{unknown_total} speeches need overrides in {overrides_path}")


def load_casting(build_dir: Path) -> dict[str, str]:
    casting_path = build_dir / "casting.json"
    if not casting_path.exists():
        casting_path.parent.mkdir(parents=True, exist_ok=True)
        casting_path.write_text(json.dumps(DEFAULT_CASTING, indent=2),
                                encoding="utf-8", newline="\n")
        print(f"Wrote default casting table: {casting_path}")
    return json.loads(casting_path.read_text(encoding="utf-8"))


def voice_for(speaker: str, casting: dict[str, str]) -> str:
    if speaker in casting:
        return casting[speaker]
    if speaker in FEMALE:
        return casting["_default_female"]
    return casting["_default_male"]


def cmd_prepare(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir)
    build_dir = Path(args.build_dir)
    seg_dir = build_dir / "segments"
    chunk_dir = build_dir / "chunks"
    casting = load_casting(build_dir)

    manifest = {"build_dir": str(build_dir), "books": []}
    total_chunks = 0

    for book_id in book_ids(source_dir, args.books):
        seg_path = seg_dir / f"{book_id}.json"
        if not seg_path.exists():
            raise SystemExit(f"Missing {seg_path}. Run tag first.")
        segments = json.loads(seg_path.read_text(encoding="utf-8"))
        unknown = [s for s in segments if s["speaker"] == "UNKNOWN"]
        if unknown:
            raise SystemExit(
                f"{book_id} has {len(unknown)} UNKNOWN speeches; fix "
                f"overrides.json and rerun tag.")

        # Merge adjacent segments sharing a voice, then size-split.
        merged: list[dict] = []
        for seg in segments:
            text = seg["text"]
            if getattr(args, "join_lines", False):
                paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
                joined_paragraphs = []
                for p in paragraphs:
                    lines = [l.strip() for l in p.splitlines() if l.strip()]
                    joined_paragraphs.append(" ".join(lines))
                text = "\n\n".join(joined_paragraphs)
            voice = voice_for(seg["speaker"], casting)
            speaker = seg["speaker"]
            if merged and merged[-1]["voice"] == voice and merged[-1]["speaker"] == speaker:
                merged[-1]["text"] += "\n\n" + text
            else:
                merged.append({"speaker": speaker, "voice": voice, "text": text})

        this_chunk_dir = chunk_dir / book_id
        if this_chunk_dir.exists():
            for old in this_chunk_dir.glob("chunk-*.txt"):
                old.unlink()
        this_chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_items = []
        index = 0
        for seg in merged:
            for piece in split_long_text(seg["text"], args.max_chars):
                index += 1
                chunk_path = this_chunk_dir / f"chunk-{index:03d}.txt"
                chunk_path.write_text(piece, encoding="utf-8", newline="\n")
                chunk_items.append({
                    "index": index,
                    "path": str(chunk_path),
                    "characters": len(piece),
                    "speaker": seg["speaker"],
                    "voice": seg["voice"],
                })
        total_chunks += index
        manifest["books"].append({"book": book_id, "chunks": chunk_items})
        voices = sorted({c["voice"] for c in chunk_items})
        print(f"{book_id}: {index} chunks, voices: {', '.join(voices)}")

    (build_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print(f"\nPrepared {total_chunks} chunks. Manifest: {build_dir / 'manifest.json'}")


def cmd_synthesize(args: argparse.Namespace) -> None:
    import os
    import time
    import urllib.error

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY or pass --api-key.")

    build_dir = Path(args.build_dir)
    manifest = json.loads((build_dir / "manifest.json").read_text(encoding="utf-8"))
    audio_dir = build_dir / "audio-chunks"

    pronunciations = load_pronunciations(args.pronunciations_file)
    replacement_pattern = None
    if getattr(args, "phonetic_replace", False) and pronunciations:
        replacement_pattern = build_replacement_regex(list(pronunciations.keys()))

    selected = set(args.books or [])
    done = skipped = failed = 0
    for book in manifest["books"]:
        book_id = book["book"]
        if selected and book_id not in selected:
            continue
        out_book_dir = audio_dir / book_id
        out_book_dir.mkdir(parents=True, exist_ok=True)

        for chunk in book["chunks"]:
            out_path = out_book_dir / f"chunk-{chunk['index']:03d}.{args.format}"
            temp_path = out_path.with_suffix(out_path.suffix + ".tmp")
            if out_path.exists() and out_path.stat().st_size > 0 and not args.force:
                skipped += 1
                continue

            speaker = chunk["speaker"]
            instructions = (NARRATOR_INSTRUCTIONS if speaker == "narrator"
                            else character_instructions(speaker))
            text = Path(chunk["path"]).read_text(encoding="utf-8")
            if replacement_pattern:
                text = replace_names(text, pronunciations, replacement_pattern)
            print(f"Synthesizing {book_id} chunk {chunk['index']:03d} "
                  f"({speaker} / {chunk['voice']})...")

            for attempt in range(1, args.retries + 2):
                try:
                    audio = speech_request(
                        api_key=api_key, text=text, model=args.model,
                        voice=chunk["voice"], response_format=args.format,
                        speed=args.speed, instructions=instructions,
                        timeout=args.timeout)
                    temp_path.write_bytes(audio)
                    temp_path.replace(out_path)
                    done += 1
                    break
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode("utf-8", errors="replace")
                    if attempt <= args.retries and exc.code in {408, 409, 429, 500, 502, 503, 504}:
                        wait = min(60, 2 ** attempt)
                        print(f"HTTP {exc.code}; retrying in {wait}s.")
                        time.sleep(wait)
                        continue
                    failed += 1
                    print(f"FAILED {book_id} chunk {chunk['index']:03d}: HTTP {exc.code} {body}")
                    break
                except Exception as exc:
                    if attempt <= args.retries:
                        wait = min(60, 2 ** attempt)
                        print(f"{type(exc).__name__}: {exc}; retrying in {wait}s.")
                        time.sleep(wait)
                        continue
                    failed += 1
                    print(f"FAILED {book_id} chunk {chunk['index']:03d}: {exc}")
                    break

    print(f"Synthesis complete: {done} generated, {skipped} skipped, {failed} failed.")


def cmd_concat(args: argparse.Namespace) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH.")

    build_dir = Path(args.build_dir)
    manifest = json.loads((build_dir / "manifest.json").read_text(encoding="utf-8"))
    audio_dir = build_dir / "audio-chunks"
    books_dir = build_dir / "books"
    books_dir.mkdir(parents=True, exist_ok=True)

    selected = set(args.books or [])
    for book in manifest["books"]:
        book_id = book["book"]
        if selected and book_id not in selected:
            continue
        chunks = sorted((audio_dir / book_id).glob(f"chunk-*.{args.format}"))
        expected = len(book["chunks"])
        if len(chunks) != expected:
            print(f"SKIP {book_id}: {len(chunks)}/{expected} chunks present.")
            continue
        list_path = audio_dir / book_id / "concat.txt"
        list_path.write_text(
            "".join(f"file '{c.as_posix()}'\n" for c in chunks),
            encoding="utf-8", newline="\n")
        out_path = books_dir / f"{book_id}.{args.format}"
        print(f"Concatenating {book_id} -> {out_path}")
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
             "-c", "copy", str(out_path)],
            check=True, capture_output=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
        p.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
        p.add_argument("--books", nargs="*", help="Limit to book ids such as book-01")

    tag_parser = sub.add_parser("tag", help="segment and attribute speakers")
    common(tag_parser)

    prep_parser = sub.add_parser("prepare", help="cast voices and chunk")
    common(prep_parser)
    prep_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    prep_parser.add_argument("--join-lines", action="store_true", help="Join lines within paragraphs for natural flow")

    synth_parser = sub.add_parser("synthesize", help="generate TTS chunks")
    common(synth_parser)
    synth_parser.add_argument("--api-key")
    synth_parser.add_argument("--model", default=DEFAULT_MODEL)
    synth_parser.add_argument("--format", default=DEFAULT_FORMAT)
    synth_parser.add_argument("--speed", type=float, default=1.0)
    synth_parser.add_argument("--pronunciations-file", default=DEFAULT_PRONUNCIATIONS_FILE, help="TSV file with headword and pronunciation columns")
    synth_parser.add_argument("--phonetic-replace", action="store_true", help="Replace names in text with phonetic spellings on-the-fly")
    synth_parser.add_argument("--timeout", type=int, default=120)
    synth_parser.add_argument("--retries", type=int, default=3)
    synth_parser.add_argument("--force", action="store_true")

    concat_parser = sub.add_parser("concat", help="join chunks per book")
    common(concat_parser)
    concat_parser.add_argument("--format", default=DEFAULT_FORMAT)

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    {"tag": cmd_tag, "prepare": cmd_prepare,
     "synthesize": cmd_synthesize, "concat": cmd_concat}[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
