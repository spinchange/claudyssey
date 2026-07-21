"""Build a single-narrator OpenAI TTS audiobook from the Odyssey Markdown.

The pipeline is intentionally staged:

1. prepare    Clean copied Markdown into narration text and API-sized chunks.
2. synthesize Generate one audio file per chunk with OpenAI text-to-speech.
3. concat     Join generated chunks into one file per book with ffmpeg.
              Optionally join the books into one full audiobook file.
4. all        Run prepare, synthesize, and concat in order.

The script defaults to reading from ./audiobook-source and writing derived
files under ./audiobook-build. It never edits source Markdown files.
"""

from __future__ import annotations

import argparse
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


FOOTNOTE_REF_RE = re.compile(r"\[\^L\d+\]")
LINE_NUMBER_RE = re.compile(r"^\s*\d+\s+")
NOTE_DEF_RE = re.compile(r"^\[\^L\d+\]:")


def book_files(source_dir: Path) -> list[Path]:
    return sorted(source_dir.glob("book-*.md"))


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


def synthesize(args: argparse.Namespace) -> None:
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY or pass --api-key.")

    build_dir = Path(args.build_dir)
    manifest = load_manifest(build_dir)
    audio_dir = build_dir / "audio-chunks"
    audio_dir.mkdir(parents=True, exist_ok=True)

    selected_books = set(args.books or [])
    done = 0
    skipped = 0
    failed = 0

    for book in manifest["books"]:
        book_id = book["book"]
        if selected_books and book_id not in selected_books:
            continue

        out_book_dir = audio_dir / book_id
        out_book_dir.mkdir(parents=True, exist_ok=True)

        for chunk in book["chunks"]:
            chunk_path = Path(chunk["path"])
            out_path = out_book_dir / f"chunk-{chunk['index']:03d}.{args.format}"
            temp_path = out_path.with_suffix(out_path.suffix + ".tmp")

            if out_path.exists() and out_path.stat().st_size > 0 and not args.force:
                skipped += 1
                continue

            text = chunk_path.read_text(encoding="utf-8")
            print(f"Synthesizing {book_id} chunk {chunk['index']:03d}...")

            for attempt in range(1, args.retries + 2):
                try:
                    audio = speech_request(
                        api_key=api_key,
                        text=text,
                        model=args.model,
                        voice=args.voice,
                        response_format=args.format,
                        speed=args.speed,
                        instructions=args.instructions,
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

    synth_parser = subparsers.add_parser("synthesize", help="generate TTS chunks")
    add_common_arguments(synth_parser)
    synth_parser.add_argument("--api-key")
    synth_parser.add_argument("--model", default=DEFAULT_MODEL)
    synth_parser.add_argument("--voice", default=DEFAULT_VOICE)
    synth_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    synth_parser.add_argument("--speed", type=float, default=1.0)
    synth_parser.add_argument("--instructions", default="Read as a clear, measured, single-narrator literary audiobook. Keep direct speech natural but do not perform multiple character voices.")
    synth_parser.add_argument("--timeout", type=int, default=120)
    synth_parser.add_argument("--retries", type=int, default=3)
    synth_parser.add_argument("--force", action="store_true")
    synth_parser.add_argument("--stop-on-error", action="store_true")
    synth_parser.add_argument("--books", nargs="*", help="Limit to book ids such as book-01 book-02")

    concat_parser = subparsers.add_parser("concat", help="join chunks into per-book files")
    add_common_arguments(concat_parser)
    concat_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    concat_parser.add_argument("--force", action="store_true")
    concat_parser.add_argument("--full", action="store_true", help="Also join per-book files into one audiobook file")
    concat_parser.add_argument("--full-name", default="odyssey", help="Base filename for --full output")
    concat_parser.add_argument("--stop-on-error", action="store_true")
    concat_parser.add_argument("--books", nargs="*", help="Limit to book ids such as book-01 book-02")

    all_parser = subparsers.add_parser("all", help="prepare, synthesize, and concat")
    add_common_arguments(all_parser)
    all_parser.add_argument("--api-key")
    all_parser.add_argument("--model", default=DEFAULT_MODEL)
    all_parser.add_argument("--voice", default=DEFAULT_VOICE)
    all_parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "opus", "aac", "flac", "wav", "pcm"])
    all_parser.add_argument("--speed", type=float, default=1.0)
    all_parser.add_argument("--instructions", default="Read as a clear, measured, single-narrator literary audiobook. Keep direct speech natural but do not perform multiple character voices.")
    all_parser.add_argument("--timeout", type=int, default=120)
    all_parser.add_argument("--retries", type=int, default=3)
    all_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
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
