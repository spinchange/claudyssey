#!/usr/bin/env python3
"""Regenerate the audio chunks made stale by the 2026-08-21 errata patches.

Reads stale-chunks.json (written by the errata pass), deletes exactly those
chunk mp3s, re-synthesizes them with each book's recorded production settings,
re-concatenates the affected book files, and rebuilds the four volume mp3s.

Requires OPENAI_API_KEY in the environment and ffmpeg on PATH.

    python regen-stale.py            # do everything
    python regen-stale.py --dry-run  # show what would happen, touch nothing
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent.parent  # repo root (odyssey/)
TOOL = ROOT / "tools" / "build_audiobook.py"
SOURCE = BUILD.parent      # hexameter-retranslation/

VOLUMES = {
    "telemachy-books-01-04.mp3": range(1, 5),
    "homecoming-books-05-08.mp3": range(5, 9),
    "great-wanderings-books-09-12.mp3": range(9, 13),
    "odysseus-on-ithaca-books-13-24.mp3": range(13, 25),
}


def settings_for(book_id: str) -> dict:
    per_book = BUILD / f"production-settings-{book_id}.json"
    path = per_book if per_book.exists() else BUILD / "production-settings.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str], dry: bool) -> None:
    print("  $", " ".join(str(c) for c in cmd))
    if not dry:
        subprocess.run([str(c) for c in cmd], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    stale = json.loads((BUILD / "stale-chunks.json").read_text(encoding="utf-8"))["stale"]
    affected = sorted(stale)

    # 1. Move exactly the stale chunk mp3s aside (synthesize skips existing
    # files).  Google Drive-mounted workspaces may deny unlinking existing
    # files while allowing rename, so retain recoverable backups.
    for book_id, indexes in sorted(stale.items()):
        for i in indexes:
            mp3 = BUILD / "audio-chunks" / book_id / f"chunk-{i:03d}.mp3"
            backup = mp3.with_suffix(mp3.suffix + ".stale")
            print(f"move {mp3.relative_to(BUILD)} -> {backup.name}" +
                  ("" if mp3.exists() else "  (already absent)"))
            if not dry and mp3.exists():
                if backup.exists():
                    raise SystemExit(f"stale backup already exists: {backup}")
                mp3.rename(backup)

    # 2. Re-synthesize only those chunks, per book, with its recorded settings.
    for book_id, indexes in sorted(stale.items()):
        s = settings_for(book_id)
        cmd = [sys.executable, TOOL, "synthesize",
               "--source-dir", SOURCE, "--build-dir", BUILD,
               "--provider", s.get("provider", "openai"),
               "--model", s["model"], "--voice", s["voice"],
               "--speed", str(s["speed"]), "--format", s.get("response_format", "mp3"),
               "--instructions", s["instructions"],
               "--books", book_id, "--chunks", *[str(i) for i in indexes]]
        fixes = s.get("pronunciation_fixes")
        if fixes and (BUILD / fixes).exists():
            cmd += ["--pronunciations-file", BUILD / fixes]
        if "max_pronunciations" in s:
            cmd += ["--max-pronunciations", str(s["max_pronunciations"])]
        print(f"synthesize {book_id} chunks {indexes}")
        run(cmd, dry)

    # 3. Re-concatenate the affected book files.
    run([sys.executable, TOOL, "concat", "--source-dir", SOURCE, "--build-dir", BUILD,
         "--force", "--books", *affected], dry)

    # 4. Rebuild the four listening volumes from the per-book mp3s.
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        if dry:
            ffmpeg = "ffmpeg"
            print("note: ffmpeg not on PATH in this shell; volume commands shown anyway")
        else:
            raise SystemExit("ffmpeg not found on PATH")
    books_dir = BUILD / "books"
    for volume, span in VOLUMES.items():
        listing = BUILD / f"{volume}.regen-concat.txt"
        entries = [books_dir / f"book-{n:02d}.mp3" for n in span]
        missing = [p for p in entries if not p.exists() and not dry]
        if missing:
            print(f"skip {volume}: missing {[m.name for m in missing]}")
            continue
        if not dry:
            listing.write_text(
                "".join(f"file '{p.as_posix()}'\n" for p in entries), encoding="utf-8")
        out = books_dir / volume
        run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", out], dry)
        if not dry:
            listing.unlink()
            top = BUILD / volume  # refresh top-level copy where one exists
            if top.exists():
                shutil.copyfile(out, top)

    print("done" + (" (dry run)" if dry else ""))


if __name__ == "__main__":
    main()
