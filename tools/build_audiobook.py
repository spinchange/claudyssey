"""Build a single-narrator OpenAI or ElevenLabs audiobook from the Odyssey Markdown.

The pipeline is intentionally staged:

1. prepare    Clean copied Markdown into narration text and API-sized chunks.
2. synthesize Generate one audio file per chunk with the selected TTS provider.
3. concat     Join generated chunks into one file per book with ffmpeg.
              Optionally join the books into one full audiobook file.
4. all        Run prepare, synthesize, and concat in order.

The script defaults to reading from ./audiobook-source and writing derived
files under ./audiobook-build. It never edits source Markdown files.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = ROOT / "audiobook-source"
DEFAULT_BUILD_DIR = ROOT / "audiobook-build"

DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "fable"
DEFAULT_FORMAT = "mp3"
DEFAULT_MAX_CHARS = 3800
API_URL = "https://api.openai.com/v1/audio/speech"

ELEVEN_API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_ELEVEN_MODEL = "eleven_multilingual_v2"
DEFAULT_ELEVEN_VOICE = "George"
DEFAULT_ELEVEN_OUTPUT_FORMAT = "mp3_44100_128"
# Characters of neighboring-chunk text sent as previous_text/next_text so
# ElevenLabs keeps prosody continuous across chunk boundaries.
ELEVEN_STITCH_CHARS = 600

DEFAULT_PRON_PATH = ROOT / "index" / "pronunciations.tsv"
DEFAULT_PRONUNCIATIONS_FILE = str(DEFAULT_PRON_PATH) if DEFAULT_PRON_PATH.exists() else None


FOOTNOTE_REF_RE = re.compile(r"\[\^L\d+\]")
LINE_NUMBER_RE = re.compile(r"^\s*\d+\s+")
NOTE_DEF_RE = re.compile(r"^\[\^L\d+\]:")
CAPITALIZED_WORD_RE = re.compile(r"\b[A-Z][A-Za-z]+\b")


def book_files(source_dir: Path) -> list[Path]:
    # Match canonical book sources only. Companion files such as
    # ``book-01-performance.md`` may live beside a book but must not become
    # accidental audiobook chapters.
    return sorted(
        path
        for path in source_dir.glob("book-*.md")
        if re.fullmatch(r"book-\d{2}\.md", path.name)
    )


def clean_markdown(text: str) -> str:
    """Strip apparatus and line markers while preserving readable paragraphs."""
    cleaned: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.strip() == "## Notes":
            break
        if NOTE_DEF_RE.match(line):
            continue

        line = FOOTNOTE_REF_RE.sub("", line)
        line = LINE_NUMBER_RE.sub("", line)

        stripped = line.strip()
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        if len(stripped) >= 2 and stripped.startswith("*") and stripped.endswith("*"):
            stripped = stripped[1:-1].strip()

        # Remove simple Markdown emphasis markers that are not meant to be read.
        stripped = stripped.replace("**", "").replace("__", "")
        stripped = stripped.replace("*", "").replace("_", "")

        if stripped:
            cleaned.append(stripped)
        elif cleaned and cleaned[-1] != "":
            cleaned.append("")

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned) + "\n"


def split_sentences(paragraph: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;:])\s+", paragraph.strip())
    return [p for p in parts if p]


def split_long_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks under max_chars, preferring paragraph boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush_current() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    def append_unit(unit: str) -> None:
        nonlocal current
        sep = "\n\n" if current else ""
        if len(current) + len(sep) + len(unit) <= max_chars:
            current = f"{current}{sep}{unit}" if current else unit
            return
        flush_current()
        if len(unit) <= max_chars:
            current = unit
            return

        # Fall back from paragraph to sentence, then word chunks.
        for sentence in split_sentences(unit):
            if len(sentence) <= max_chars:
                append_unit(sentence)
                continue
            words = sentence.split()
            piece = ""
            for word in words:
                sep2 = " " if piece else ""
                if len(piece) + len(sep2) + len(word) > max_chars:
                    if piece:
                        append_unit(piece)
                    piece = word
                else:
                    piece = f"{piece}{sep2}{word}" if piece else word
            if piece:
                append_unit(piece)

    for paragraph in paragraphs:
        append_unit(paragraph)
    flush_current()
    return chunks


def prepare(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir)
    build_dir = Path(args.build_dir)
    clean_dir = build_dir / "clean"
    chunk_dir = build_dir / "chunks"
    clean_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    files = book_files(source_dir)
    if not files:
        raise SystemExit(f"No book-*.md files found in {source_dir}")

    manifest = {
        "source_dir": str(source_dir),
        "build_dir": str(build_dir),
        "max_chars": args.max_chars,
        "books": [],
    }

    total_chars = 0
    total_chunks = 0

    for src in files:
        book_id = src.stem
        text = src.read_text(encoding="utf-8")
        cleaned = clean_markdown(text)
        if getattr(args, "join_lines", False):
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
            joined_paragraphs = []
            for p in paragraphs:
                lines = [l.strip() for l in p.splitlines() if l.strip()]
                joined_paragraphs.append(" ".join(lines))
            cleaned = "\n\n".join(joined_paragraphs) + "\n"
        chunks = split_long_text(cleaned, args.max_chars)

        clean_path = clean_dir / f"{book_id}.txt"
        clean_path.write_text(cleaned, encoding="utf-8", newline="\n")

        this_chunk_dir = chunk_dir / book_id
        if this_chunk_dir.exists():
            for old in this_chunk_dir.glob("chunk-*.txt"):
                old.unlink()
        this_chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_items = []
        for index, chunk in enumerate(chunks, 1):
            chunk_path = this_chunk_dir / f"chunk-{index:03d}.txt"
            chunk_path.write_text(chunk, encoding="utf-8", newline="\n")
            chunk_items.append({
                "index": index,
                "path": str(chunk_path),
                "characters": len(chunk),
            })

        total_chars += len(cleaned)
        total_chunks += len(chunks)
        manifest["books"].append({
            "book": book_id,
            "source": str(src),
            "clean_text": str(clean_path),
            "characters": len(cleaned),
            "chunks": chunk_items,
        })
        print(f"{book_id}: {len(cleaned):6d} chars -> {len(chunks):2d} chunks")

    manifest["total_characters"] = total_chars
    manifest["total_chunks"] = total_chunks
    (build_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(f"\nPrepared {len(files)} books, {total_chars} chars, {total_chunks} chunks.")
    print(f"Manifest: {build_dir / 'manifest.json'}")


def load_manifest(build_dir: Path) -> dict:
    manifest_path = build_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing {manifest_path}. Run prepare first.")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_pronunciations(path: str | None) -> dict[str, str]:
    if not path:
        return {}

    pronunciations: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if not row or not row[0] or row[0].startswith("#"):
                continue
            headword = row[0].strip()
            say = row[1].strip() if len(row) > 1 else ""
            if headword and say:
                pronunciations[headword] = say

    # Check for TTS-specific overrides to adjust human respellings for the machine
    override_path = Path(path).parent / "pronunciations-tts-overrides.json"
    if override_path.exists():
        try:
            with open(override_path, encoding="utf-8") as handle:
                overrides = json.load(handle)
                for headword, say in overrides.items():
                    pronunciations[headword] = say
            print(f"Loaded {len(overrides)} pronunciation overrides from {override_path.name}")
        except Exception as e:
            print(f"Warning: Failed to load pronunciation overrides: {e}")

    return pronunciations


def build_replacement_regex(names: list[str]) -> re.Pattern:
    sorted_names = sorted(names, key=len, reverse=True)
    escaped_names = [re.escape(name) for name in sorted_names]
    pattern_str = r"\b(" + "|".join(escaped_names) + r")\b"
    return re.compile(pattern_str, re.IGNORECASE)


def replace_names(text: str, pronunciations: dict[str, str], pattern: re.Pattern) -> str:
    def repl(match):
        word = match.group(1)
        key = None
        for k in pronunciations:
            if k.lower() == word.lower():
                key = k
                break
        if key is None:
            return word
        pron = pronunciations[key].lower()
        if word.isupper():
            return pron.upper()
        elif word[0].isupper():
            return pron[0].upper() + pron[1:]
        return pron
    return pattern.sub(repl, text)


def pronunciation_instruction(
    book: dict,
    pronunciations: dict[str, str],
    max_pronunciations: int,
) -> str:
    if not pronunciations:
        return ""

    clean_text = Path(book["clean_text"]).read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for match in CAPITALIZED_WORD_RE.findall(clean_text):
        counts[match] = counts.get(match, 0) + 1
    items = []

    names = [name for name in counts if name in pronunciations]
    names.sort(key=lambda name: (name != "Zeus", -counts[name], name))

    for name in names[:max_pronunciations]:
        say = pronunciations.get(name)
        if not say:
            continue
        if name == "Zeus":
            items.append("Zeus=ZOOS, one syllable, rhymes with moose, never zee-oos")
        else:
            items.append(f"{name}={say}")

    if not items:
        return ""

    return " Use these pronunciations consistently: " + "; ".join(items) + "."


def speech_request(
    *,
    api_key: str,
    text: str,
    model: str,
    voice: str,
    response_format: str,
    speed: float,
    instructions: str | None,
    timeout: int,
) -> bytes:
    payload = {
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": response_format,
        "speed": speed,
    }
    if instructions:
        payload["instructions"] = instructions

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def eleven_get_json(api_key: str, path: str, timeout: int = 30) -> dict:
    request = urllib.request.Request(
        f"{ELEVEN_API_BASE}{path}",
        headers={"xi-api-key": api_key},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def eleven_resolve_voice(api_key: str, voice: str, timeout: int = 30) -> str:
    """Accept a raw voice_id, or resolve a voice name via the voices API."""
    if voice.startswith("id:"):
        return voice[3:]
    if re.fullmatch(r"[A-Za-z0-9_-]{16,64}", voice) and any(c.isdigit() for c in voice):
        return voice
    try:
        data = eleven_get_json(api_key, "/voices", timeout)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in {401, 403} and "voices_read" in body:
            raise SystemExit(
                f"Cannot resolve ElevenLabs voice {voice!r} by name: this API key "
                "does not have voices_read permission. Pass the voice ID directly "
                "with --voice id:VOICE_ID (synthesize) or --voice-id VOICE_ID "
                "(audition), or enable Voices: Read on the key."
            ) from exc
        raise
    names = {}
    for entry in data.get("voices", []):
        names[entry["name"].lower()] = entry["voice_id"]
    voice_id = names.get(voice.lower())
    if not voice_id:
        available = ", ".join(sorted(names)) or "(none)"
        raise SystemExit(f"Voice {voice!r} not found. Available: {available}")
    return voice_id


def eleven_speech_request(
    *,
    api_key: str,
    text: str,
    model: str,
    voice_id: str,
    output_format: str,
    voice_settings: dict,
    previous_text: str | None,
    next_text: str | None,
    timeout: int,
) -> bytes:
    payload: dict = {
        "text": text,
        "model_id": model,
        "voice_settings": voice_settings,
    }
    if previous_text:
        payload["previous_text"] = previous_text
    if next_text:
        payload["next_text"] = next_text

    request = urllib.request.Request(
        f"{ELEVEN_API_BASE}/text-to-speech/{voice_id}?output_format={output_format}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def eleven_voice_settings(args: argparse.Namespace) -> dict:
    settings = {
        "stability": args.stability,
        "similarity_boost": args.similarity_boost,
        "style": args.style,
        "use_speaker_boost": True,
    }
    if getattr(args, "speed", 1.0) != 1.0:
        settings["speed"] = args.speed
    return settings


def synthesize(args: argparse.Namespace) -> None:
    provider = getattr(args, "provider", "openai")
    if provider == "elevenlabs":
        api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise SystemExit("Set ELEVENLABS_API_KEY or pass --api-key.")
        model = args.model if args.model != DEFAULT_MODEL else DEFAULT_ELEVEN_MODEL
        voice = args.voice if args.voice != DEFAULT_VOICE else DEFAULT_ELEVEN_VOICE
        voice_id = eleven_resolve_voice(api_key, voice)
        voice_settings = eleven_voice_settings(args)
    else:
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("Set OPENAI_API_KEY or pass --api-key.")

    build_dir = Path(args.build_dir)
    manifest = load_manifest(build_dir)
    pronunciations = load_pronunciations(args.pronunciations_file)
    replacement_pattern = None
    if getattr(args, "phonetic_replace", False) and pronunciations:
        replacement_pattern = build_replacement_regex(list(pronunciations.keys()))

    audio_dir = build_dir / "audio-chunks"
    audio_dir.mkdir(parents=True, exist_ok=True)

    selected_books = set(args.books or [])
    selected_chunks = set(getattr(args, "chunks", None) or [])
    done = 0
    skipped = 0
    failed = 0

    for book in manifest["books"]:
        book_id = book["book"]
        if selected_books and book_id not in selected_books:
            continue

        out_book_dir = audio_dir / book_id
        out_book_dir.mkdir(parents=True, exist_ok=True)
        book_instructions = ""
        if provider == "openai":
            book_instructions = args.instructions + pronunciation_instruction(
                book,
                pronunciations,
                args.max_pronunciations,
            )

        def chunk_text(item: dict) -> str:
            text = Path(item["path"]).read_text(encoding="utf-8")
            if replacement_pattern:
                text = replace_names(text, pronunciations, replacement_pattern)
            return text

        chunk_list = book["chunks"]
        for position, chunk in enumerate(chunk_list):
            if selected_chunks and chunk["index"] not in selected_chunks:
                continue
            out_path = out_book_dir / f"chunk-{chunk['index']:03d}.{args.format}"
            temp_path = out_path.with_suffix(out_path.suffix + ".tmp")

            if out_path.exists() and out_path.stat().st_size > 0 and not args.force:
                skipped += 1
                continue

            text = chunk_text(chunk)
            previous_text = None
            next_text = None
            if provider == "elevenlabs":
                if position > 0:
                    previous_text = chunk_text(chunk_list[position - 1])[-ELEVEN_STITCH_CHARS:]
                if position + 1 < len(chunk_list):
                    next_text = chunk_text(chunk_list[position + 1])[:ELEVEN_STITCH_CHARS]
            print(f"Synthesizing {book_id} chunk {chunk['index']:03d}...")

            for attempt in range(1, args.retries + 2):
                try:
                    if provider == "elevenlabs":
                        audio = eleven_speech_request(
                            api_key=api_key,
                            text=text,
                            model=model,
                            voice_id=voice_id,
                            output_format=args.output_format,
                            voice_settings=voice_settings,
                            previous_text=previous_text,
                            next_text=next_text,
                            timeout=args.timeout,
                        )
                    else:
                        audio = speech_request(
                            api_key=api_key,
                            text=text,
                            model=args.model,
                            voice=args.voice,
                            response_format=args.format,
                            speed=args.speed,
                            instructions=book_instructions,
                            timeout=args.timeout,
                        )
                    temp_path.write_bytes(audio)
                    temp_path.replace(out_path)
                    done += 1
                    break
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode("utf-8", errors="replace")
                    retryable = exc.code in {408, 409, 429, 500, 502, 503, 504}
                    if attempt <= args.retries + 1 and retryable:
                        wait = min(60, 2 ** attempt)
                        print(f"HTTP {exc.code}; retrying in {wait}s.")
                        time.sleep(wait)
                        continue
                    failed += 1
                    print(f"FAILED {book_id} chunk {chunk['index']:03d}: HTTP {exc.code} {body}")
                    if args.stop_on_error:
                        raise SystemExit(1)
                    break
                except Exception as exc:
                    if attempt <= args.retries + 1:
                        wait = min(60, 2 ** attempt)
                        print(f"{type(exc).__name__}: {exc}; retrying in {wait}s.")
                        time.sleep(wait)
                        continue
                    failed += 1
                    print(f"FAILED {book_id} chunk {chunk['index']:03d}: {exc}")
                    if args.stop_on_error:
                        raise SystemExit(1)
                    break

    print(f"Synthesis complete: {done} generated, {skipped} skipped, {failed} failed.")


def eleven_api_key(args: argparse.Namespace) -> str:
    api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit("Set ELEVENLABS_API_KEY or pass --api-key.")
    return api_key


def quota(args: argparse.Namespace) -> None:
    data = eleven_get_json(eleven_api_key(args), "/user/subscription")
    used = data.get("character_count", 0)
    limit = data.get("character_limit", 0)
    print(f"Tier:      {data.get('tier')}")
    print(f"Credits:   {used} used of {limit} ({limit - used} remaining)")
    print(f"Status:    {data.get('status')}")


def audition(args: argparse.Namespace) -> None:
    """Generate short samples of the same passage in several voices."""
    api_key = eleven_api_key(args)
    build_dir = Path(args.build_dir)

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    else:
        clean_path = build_dir / "clean" / f"{args.book}.txt"
        if not clean_path.exists():
            raise SystemExit(f"Missing {clean_path}. Run prepare first or pass --text-file.")
        text = clean_path.read_text(encoding="utf-8")

    if len(text) > args.text_chars:
        cut = text[:args.text_chars]
        last_end = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("!"), cut.rfind("?"))
        text = cut[: last_end + 1] if last_end > 0 else cut

    if getattr(args, "phonetic_replace", False):
        pronunciations = load_pronunciations(args.pronunciations_file)
        pattern = build_replacement_regex(list(pronunciations.keys()))
        if pronunciations:
            text = replace_names(text, pronunciations, pattern)

    out_dir = build_dir / "auditions"
    out_dir.mkdir(parents=True, exist_ok=True)
    voice_settings = eleven_voice_settings(args)
    print(f"Sample text ({len(text)} chars):\n---\n{text}\n---")

    requested_voices = args.voices
    if args.voice_id:
        requested_voices = [f"{args.voice_name}={args.voice_id}"]

    for voice in requested_voices:
        # "Name=voice_id" and --voice-id skip the voices API, which scoped keys
        # may intentionally be unable to read.
        if "=" in voice:
            voice, voice_id = voice.split("=", 1)
        else:
            voice_id = eleven_resolve_voice(api_key, voice)
        print(f"Auditioning {voice} ({voice_id})...")
        audio = eleven_speech_request(
            api_key=api_key,
            text=text,
            model=args.model,
            voice_id=voice_id,
            output_format=args.output_format,
            voice_settings=voice_settings,
            previous_text=None,
            next_text=None,
            timeout=args.timeout,
        )
        out_path = out_dir / f"{voice.lower().replace(' ', '-')}.mp3"
        out_path.write_bytes(audio)
        print(f"  -> {out_path}")


def concat(args: argparse.Namespace) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH; install ffmpeg or skip concat.")

    build_dir = Path(args.build_dir)
    manifest = load_manifest(build_dir)
    audio_dir = build_dir / "audio-chunks"
    books_dir = build_dir / "books"
    books_dir.mkdir(parents=True, exist_ok=True)
    selected_books = set(args.books or [])
    book_outputs: list[Path] = []

    for book in manifest["books"]:
        book_id = book["book"]
        if selected_books and book_id not in selected_books:
            continue

        chunks = sorted((audio_dir / book_id).glob(f"chunk-*.{args.format}"))
        if not chunks:
            print(f"Skipping {book_id}: no audio chunks found.")
            continue

        list_path = books_dir / f"{book_id}-concat.txt"
        lines = []
        for chunk in chunks:
            safe_path = chunk.resolve().as_posix().replace("'", "'\\''")
            lines.append(f"file '{safe_path}'")
        list_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        out_path = books_dir / f"{book_id}.{args.format}"
        cmd = [
            ffmpeg,
            "-y" if args.force else "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(out_path),
        ]
        print(f"Concatenating {book_id} -> {out_path}")
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            print(result.stdout)
            if args.stop_on_error:
                raise SystemExit(result.returncode)
        elif out_path.exists():
            book_outputs.append(out_path)

    if args.full and book_outputs:
        full_list_path = books_dir / "odyssey-concat.txt"
        lines = []
        for book_path in book_outputs:
            safe_path = book_path.resolve().as_posix().replace("'", "'\\''")
            lines.append(f"file '{safe_path}'")
        full_list_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        full_path = books_dir / f"{args.full_name}.{args.format}"
        cmd = [
            ffmpeg,
            "-y" if args.force else "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(full_list_path),
            "-c",
            "copy",
            str(full_path),
        ]
        print(f"Concatenating full audiobook -> {full_path}")
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            print(result.stdout)
            if args.stop_on_error:
                raise SystemExit(result.returncode)


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="clean and chunk text")
    add_common_arguments(prepare_parser)
    prepare_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    prepare_parser.add_argument("--join-lines", action="store_true", help="Join lines within paragraphs for natural flow")

    def add_elevenlabs_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--output-format", default=DEFAULT_ELEVEN_OUTPUT_FORMAT,
                            help="ElevenLabs output format such as mp3_44100_128 or mp3_44100_192")
        parser.add_argument("--stability", type=float, default=0.5)
        parser.add_argument("--similarity-boost", type=float, default=0.75)
        parser.add_argument("--style", type=float, default=0.0)

    synth_parser = subparsers.add_parser("synthesize", help="generate TTS chunks")
    add_common_arguments(synth_parser)
    synth_parser.add_argument("--provider", choices=["openai", "elevenlabs"], default="openai")
    add_elevenlabs_arguments(synth_parser)
    synth_parser.add_argument("--api-key")
    synth_parser.add_argument("--model", default=DEFAULT_MODEL)
    synth_parser.add_argument("--voice", default=DEFAULT_VOICE)
    synth_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    synth_parser.add_argument("--speed", type=float, default=1.0)
    synth_parser.add_argument("--instructions", default="Read as a clear, measured, single-narrator literary audiobook. Keep direct speech natural but do not perform multiple character voices.")
    synth_parser.add_argument("--pronunciations-file", default=DEFAULT_PRONUNCIATIONS_FILE, help="TSV file with headword and pronunciation columns")
    synth_parser.add_argument("--max-pronunciations", type=int, default=40, help="Maximum pronunciation entries to append per book")
    synth_parser.add_argument("--phonetic-replace", action="store_true", help="Replace names in text with phonetic spellings on-the-fly")
    synth_parser.add_argument("--timeout", type=int, default=120)
    synth_parser.add_argument("--retries", type=int, default=3)
    synth_parser.add_argument("--force", action="store_true")
    synth_parser.add_argument("--stop-on-error", action="store_true")
    synth_parser.add_argument("--books", nargs="*", help="Limit to book ids such as book-01 book-02")
    synth_parser.add_argument("--chunks", nargs="*", type=int, help="Limit synthesis to chunk indexes within the selected books")

    concat_parser = subparsers.add_parser("concat", help="join chunks into per-book files")
    add_common_arguments(concat_parser)
    concat_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    concat_parser.add_argument("--force", action="store_true")
    concat_parser.add_argument("--full", action="store_true", help="Also join per-book files into one audiobook file")
    concat_parser.add_argument("--full-name", default="odyssey", help="Base filename for --full output")
    concat_parser.add_argument("--stop-on-error", action="store_true")
    concat_parser.add_argument("--books", nargs="*", help="Limit to book ids such as book-01 book-02")

    audition_parser = subparsers.add_parser("audition", help="short ElevenLabs voice samples of one passage")
    add_common_arguments(audition_parser)
    add_elevenlabs_arguments(audition_parser)
    audition_parser.add_argument("--api-key")
    audition_parser.add_argument("--model", default=DEFAULT_ELEVEN_MODEL)
    audition_parser.add_argument("--voices", nargs="*", default=["George", "Daniel", "Brian", "Bill"])
    audition_parser.add_argument("--voice-id", help="Audition one voice ID without requiring voices_read permission")
    audition_parser.add_argument("--voice-name", default="Demodocus", help="Output label used with --voice-id")
    audition_parser.add_argument("--book", default="book-01", help="Book whose cleaned text supplies the sample")
    audition_parser.add_argument("--speed", type=float, default=1.0)
    audition_parser.add_argument("--text-file", help="Read the sample passage from this file instead")
    audition_parser.add_argument("--text-chars", type=int, default=700)
    audition_parser.add_argument("--pronunciations-file", default=DEFAULT_PRONUNCIATIONS_FILE)
    audition_parser.add_argument("--phonetic-replace", action="store_true")
    audition_parser.add_argument("--timeout", type=int, default=120)

    quota_parser = subparsers.add_parser("quota", help="show ElevenLabs subscription credit usage")
    quota_parser.add_argument("--api-key")

    all_parser = subparsers.add_parser("all", help="prepare, synthesize, and concat")
    add_common_arguments(all_parser)
    all_parser.add_argument("--provider", choices=["openai", "elevenlabs"], default="openai")
    add_elevenlabs_arguments(all_parser)
    all_parser.add_argument("--api-key")
    all_parser.add_argument("--model", default=DEFAULT_MODEL)
    all_parser.add_argument("--voice", default=DEFAULT_VOICE)
    all_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    all_parser.add_argument("--speed", type=float, default=1.0)
    all_parser.add_argument("--instructions", default="Read as a clear, measured, single-narrator literary audiobook. Keep direct speech natural but do not perform multiple character voices.")
    all_parser.add_argument("--pronunciations-file", default=DEFAULT_PRONUNCIATIONS_FILE, help="TSV file with headword and pronunciation columns")
    all_parser.add_argument("--max-pronunciations", type=int, default=40, help="Maximum pronunciation entries to append per book")
    all_parser.add_argument("--phonetic-replace", action="store_true", help="Replace names in text with phonetic spellings on-the-fly")
    all_parser.add_argument("--timeout", type=int, default=120)
    all_parser.add_argument("--retries", type=int, default=3)
    all_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    all_parser.add_argument("--join-lines", action="store_true", help="Join lines within paragraphs for natural flow")
    all_parser.add_argument("--force", action="store_true")
    all_parser.add_argument("--full", action="store_true", help="Also join per-book files into one audiobook file")
    all_parser.add_argument("--full-name", default="odyssey", help="Base filename for --full output")
    all_parser.add_argument("--stop-on-error", action="store_true")
    all_parser.add_argument("--books", nargs="*", help="Limit to book ids such as book-01 book-02")

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.command == "prepare":
        prepare(args)
    elif args.command == "synthesize":
        synthesize(args)
    elif args.command == "audition":
        audition(args)
    elif args.command == "quota":
        quota(args)
    elif args.command == "concat":
        concat(args)
    elif args.command == "all":
        prepare(args)
        synthesize(args)
        concat(args)
    else:
        raise SystemExit(f"Unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
