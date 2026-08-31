#!/usr/bin/env python3
"""Build a high-quality EPUB of the Odyssey translation.

Pipeline (leaves translation/ untouched — operates on copies):

  1. For each book, rewrite footnote identifiers to be book-unique
     ([^L1] -> [^b01-L1], both the inline marker and its ## Notes
     definition) so labels don't collide when Pandoc concatenates all
     24 books into one document. Pandoc then generates bidirectional
     links (forward ref -> note, and a return arrow note -> ref) with
     no cross-book leakage.
  2. Wrap each verse's leading line-number in a styled <span class="ln">
     so it can be set apart from the verse text (skips the argument
     line and the footnote-definition lines).
  3. Emit a title page and a source/licensing page as front matter.
  4. Invoke Pandoc: markdown -> EPUB3, split at level-1 headings so each
     book is its own chapter file, with an embedded cover, TOC, CSS,
     and Greek font.

Usage:
    python tools/build_epub.py                 # all 24 books
    python tools/build_epub.py --books 1        # just Book 1 (POC)
    python tools/build_epub.py --books 1 2 3
"""
from __future__ import annotations
import argparse, re, shutil, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translation"
BUILD = ROOT / "epub-build"
WORK = BUILD / "work"
ASSETS = BUILD / "assets"

PANDOC = os.environ.get("PANDOC") or shutil.which("pandoc") or \
    str(Path(os.environ["LOCALAPPDATA"]) / "Pandoc" / "pandoc.exe")

# [^L123]  as an inline reference (not at start of line, not a definition)
REF_RE = re.compile(r"\[\^L(\d+)\]")
# [^L123]: ...  as a note definition (start of line)
DEF_RE = re.compile(r"^\[\^L(\d+)\]:")
# A verse line: leading digits + whitespace, then text. NOT a footnote def.
VERSE_RE = re.compile(r"^(\d+)(\s+)(.*)$")


def namespace_and_format(text: str, tag: str) -> str:
    """Rewrite footnote ids to be unique to this book and format verses.

    Each numbered verse becomes its own visual line: a styled line-number
    span, then a Pandoc hard break so consecutive verses in a stanza don't
    collapse into justified prose. The hard break is markdown, so footnote
    references inside the verse are still processed.
    """
    raw = text.splitlines()
    out_lines = []
    in_notes = False
    for idx, line in enumerate(raw):
        if line.startswith("## Notes"):
            in_notes = True

        # Rewrite footnote definitions:  [^L10]: ...  ->  [^b01-L10]: ...
        m = DEF_RE.match(line)
        if m:
            line = DEF_RE.sub(rf"[^{tag}-L\1]:", line, count=1)
            # any further refs inside the note body also get namespaced below
        # Rewrite every inline reference occurrence on the line.
        line = REF_RE.sub(rf"[^{tag}-L\1]", line)

        # Wrap verse line numbers (only outside the Notes section, and not
        # on the title/argument lines which don't start with a digit).
        if not in_notes:
            vm = VERSE_RE.match(line)
            if vm:
                num, _, body = vm.groups()
                # Per-line anchor so the index can link a citation (book.line)
                # straight to this verse. bookno comes from the tag ("b07"->7).
                bookno = int(tag[1:])
                anchor = f"v{bookno}-{num}"
                line = f'<span class="ln" id="{anchor}">{num}</span> {body}'
                # Hard break unless the next line ends the stanza, so each
                # verse sits on its own line (footnote refs still processed).
                nxt = raw[idx + 1] if idx + 1 < len(raw) else ""
                if nxt.strip() and VERSE_RE.match(nxt):
                    line = line + "\\"  # trailing backslash = Pandoc hard break

        out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def title_page() -> str:
    # Custom title page (Pandoc's auto one is suppressed) so each contributor's
    # ROLE is stated, not just a bare list of names.
    return (
        '# The Odyssey {.unnumbered .hidden-title}\n\n'
        '<div class="titlepage">\n\n'
        '<p class="tp-title">The Odyssey</p>\n\n'
        '<p class="tp-sub">a line-for-line translation</p>\n\n'
        '<hr class="tp-rule"/>\n\n'
        '<p class="tp-role">from the Greek of</p>\n\n'
        '<p class="tp-name">Homer</p>\n\n'
        '<p class="tp-role">translated by</p>\n\n'
        '<p class="tp-name">Claude <span class="tp-small">(Fable 5)</span></p>\n\n'
        '<p class="tp-role">edited and produced by</p>\n\n'
        '<p class="tp-name">Chris Duffy</p>\n\n'
        '</div>\n\n'
    )


def epigraph_page() -> str:
    return (
        '<div class="epigraph-page">\n\n'
        '<p class="epigraph"><span class="greek" lang="grc">'
        "ἄνδρα μοι ἔννεπε, μοῦσα, πολύτροπον"
        "</span>\nTell me the man, Muse — the man of many turnings</p>\n\n"
        "</div>\n\n"
    )


MAP_SVG = ROOT / "art" / "map.svg"


def map_page() -> str:
    """The map (tools/build_map.py) as a front-matter chapter, facing Book 1.

    Inlined as raw HTML (the markdown input allows raw_html) rather than
    linked as an <img>, so its text sets in the embedded Gentium rather
    than whatever font a reader substitutes for text baked into a raster.
    """
    if not MAP_SVG.exists():
        return ""
    svg = MAP_SVG.read_text(encoding="utf-8")
    svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
    return (
        '# Map {.unnumbered}\n\n'
        '<div class="map-page">\n\n' + svg + '\n\n</div>\n\n'
    )


def source_page() -> str:
    return (
        "# A Note on the Text {.unnumbered}\n\n"
        "The Greek is A. T. Murray's text from the Loeb Classical Library "
        "edition (*Homer: The Odyssey*, 1919), as digitized by the Perseus "
        "Digital Library from the polytonic vulgate. The English translation "
        "is original to this project; each of the 12,107 English lines is keyed "
        "one-to-one to its Greek line.\n\n"
        "The scholarly apparatus — 1,260 notes across the poem — appears "
        "as endnotes at the close of each book. In the text a raised gold "
        "numeral marks a note; tap it to jump to the note, and tap the return "
        "arrow (↩) to come back to your place in the verse.\n\n"
        "Murray's 1919 Greek text is in the public domain; the Perseus "
        "digitization is used under CC BY-SA. Polytonic Greek is set in "
        "Gentium Plus (SIL Open Font License).\n\n"
        "The English translation is dedicated to the public domain under "
        "[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): no "
        "permission is needed to copy, adapt, or reuse it, for any purpose. "
        "The apparatus — the notes, this front matter, and the index of "
        "names — is © 2026 Chris Duffy, licensed "
        "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n\n"
    )


# A citation is book.line, optionally a range (–NN) or "ff". Book 1..24.
CITE_RE = re.compile(r"\b([12]?\d)\.(\d{1,3})(–\d{1,3}|ff)?")


def _link_citation(m: re.Match, present_books: set[int]) -> str:
    book, line, tail = int(m.group(1)), m.group(2), m.group(3) or ""
    text = m.group(0)
    if not (1 <= book <= 24) or book not in present_books:
        return text  # out of range, or that book isn't in this build
    return f"[{text}](#v{book}-{line})"


def index_page(present_books: set[int]) -> str:
    """Turn index/index.md into a back-matter chapter whose book.line
    citations link into the verse (via the per-line #v{book}-{line} anchors).
    Ranges/ff link to their first line. Leaves everything else verbatim."""
    src = (ROOT / "index" / "index.md")
    if not src.exists():
        return ""
    text = src.read_text(encoding="utf-8")
    raw = text.splitlines()
    out = []
    for i, line in enumerate(raw):
        # Only linkify lines that actually carry citations; skip the title and
        # the intro paragraph (which mentions file paths, no book.line cites).
        if CITE_RE.search(line) and not line.startswith("#"):
            line = CITE_RE.sub(lambda m: _link_citation(m, present_books), line)
        # Each entry's sub-lines (headword, gloss, Epithets, Refs, See also)
        # sit on consecutive lines with no blank between them, so markdown
        # would fuse them into one paragraph. Add a hard break to keep each on
        # its own line — but never before a blank line or a "---" separator.
        stripped = line.strip()
        nxt = raw[i + 1].strip() if i + 1 < len(raw) else ""
        if stripped and nxt and nxt != "---" and stripped != "---":
            line = line + "\\"
        out.append(line)
    body = "\n".join(out)
    # Drop the original H1 and the build-provenance intro paragraph (it names
    # source files and is meaningless to a reader); supply our own heading and
    # a reader-facing note in their place.
    body = re.sub(r"^# .*\n", "", body, count=1)
    body = re.sub(r"^\s*Every named person.*?pronunciation scheme\.\s*\n",
                  "", body, count=1, flags=re.S)
    header = (
        '# Index of Names and Places {.unnumbered #name-index}\n\n'
        "Every named person, god, people, and place in the poem, with a "
        "pronunciation (*Say:*), epithets, aliases, kin, and line citations. "
        "Each citation is a link — tap a **book.line** number to jump to that "
        "verse. Pronunciations give the traditional anglicized reading; "
        "**stress falls on the capitalized syllable**.\n\n"
        '<div class="name-index">\n\n')
    return header + body + "\n\n</div>\n\n"


def build(book_nums: list[int]) -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    (WORK / "fonts").mkdir()
    for f in ["Gentium-Regular.woff2", "Gentium-Italic.woff2"]:
        shutil.copy(ASSETS / f, WORK / "fonts" / f)

    inputs: list[Path] = []

    # Custom title page (first), with each contributor's role stated.
    tp = WORK / "00-title.md"
    tp.write_text(title_page(), encoding="utf-8")
    inputs.append(tp)

    # Epigraph (proem) page — headed so it splits into its own chapter file,
    # the heading hidden by CSS so only the Greek/English proem shows.
    epi = WORK / "00-epigraph.md"
    epi.write_text('# Proem {.unnumbered .hidden-title}\n\n' + epigraph_page(),
                   encoding="utf-8")
    inputs.append(epi)

    note = WORK / "01-note.md"
    note.write_text(source_page(), encoding="utf-8")
    inputs.append(note)

    # The map, facing Book 1 (the same convention as the print edition):
    # last thing before the poem starts, not grouped with the other notes.
    if 1 in book_nums:
        map_md = map_page()
        if map_md:
            mp = WORK / "01-map.md"
            mp.write_text(map_md, encoding="utf-8")
            inputs.append(mp)

    for n in book_nums:
        src = SRC / f"book-{n:02d}.md"
        if not src.exists():
            sys.exit(f"missing {src}")
        tag = f"b{n:02d}"
        processed = namespace_and_format(src.read_text(encoding="utf-8"), tag)
        dst = WORK / f"{n:02d}-book.md"
        dst.write_text(processed, encoding="utf-8")
        inputs.append(dst)

    # Back matter: the linked index of names (citations -> verse anchors).
    idx_md = index_page(set(book_nums))
    if idx_md:
        idx = WORK / "99-index.md"
        idx.write_text(idx_md, encoding="utf-8")
        inputs.append(idx)

    out = BUILD / ("odyssey-book01.epub" if book_nums == [1] else "odyssey.epub")

    meta = WORK / "metadata.yaml"
    meta.write_text(
        "---\n"
        "title: The Odyssey\n"
        "subtitle: A line-for-line translation\n"
        "creator:\n"
        "  - role: aut\n    text: Homer\n"
        "  - role: trl\n    text: Claude (Fable 5)\n"
        "  - role: edt\n    text: Chris Duffy\n"
        "language: en\n"
        "rights: >-\n"
        "  English translation dedicated to the public domain (CC0 1.0). "
        "Notes, front matter, and index (c) 2026 Chris Duffy, CC BY 4.0. "
        "Greek source text (Murray 1919) public domain; Perseus "
        "digitization CC BY-SA.\n"
        "...\n",
        encoding="utf-8",
    )

    cmd = [
        PANDOC,
        str(meta),
        *[str(p) for p in inputs],
        "--from=markdown+footnotes+raw_html",
        "--to=epub3",
        "--epub-title-page=false",  # we supply our own title page (00-title)
        "--split-level=1",
        f"--lua-filter={BUILD / 'backlinks.lua'}",
        "--toc", "--toc-depth=1",
        f"--epub-cover-image={ASSETS / 'cover.jpg'}",
        f"--css={BUILD / 'style.css'}",
        "--epub-embed-font=" + str(WORK / "fonts" / "Gentium-Regular.woff2"),
        "--epub-embed-font=" + str(WORK / "fonts" / "Gentium-Italic.woff2"),
        "--metadata=lang:en",
        "-o", str(out),
    ]
    print("running pandoc...")
    subprocess.run(cmd, check=True, cwd=WORK)
    print(f"\nwrote {out}  ({out.stat().st_size:,} bytes)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", nargs="*", type=int,
                    help="book numbers to include (default: all 24)")
    args = ap.parse_args()
    nums = args.books if args.books else list(range(1, 25))
    build(nums)
