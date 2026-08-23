#!/usr/bin/env python3
"""Build a press-ready PDF interior of the Odyssey translation.

This is a *print* build, not the EPUB re-flowed. What print needs that
the EPUB does not:

  - A fixed trim size and a measure chosen so that verse lines rarely
    turn over (the reader cannot change the font size on paper).
  - Line numbers every 5th verse, not every verse. Numbering all 12,107
    lines is right for a linked digital text and noise on a page.
  - Turnover indents: a verse longer than the measure continues indented
    so it still reads as one verse.
  - No hyperlinks, no return arrows. A note marker is a printed numeral.
  - Recto-forcing: each book opens on a right-hand page, with a blank
    verso inserted when needed.
  - A centered running head, and folios mirrored to the outside edge:
    bottom-left on a verso, bottom-right on a recto.
  - Black ink only: POD colour interiors cost several times mono.
  - Dictionary-style guide words on the index pages: the running head
    names the first and last entry beginning on that page.

Pipeline: translation/*.md -> one print HTML -> EPUB -> PDF (calibre).
translation/ is never modified.

The EPUB intermediate exists because calibre's html input path drops the
per-file structure that gives us running heads; the epub path keeps it.

Usage:
    python tools/build_print.py                  # all 24 books, 6x9
    python tools/build_print.py --books 1        # Book 1 only (proof)
    python tools/build_print.py --trim 5.5x8.5   # other trim sizes
    python tools/build_print.py --trim a5
"""
from __future__ import annotations
import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translation"
BUILD = ROOT / "print-build"
WORK = BUILD / "work"
EPUB_ASSETS = ROOT / "epub-build" / "assets"

EBOOK_CONVERT = (
    os.environ.get("EBOOK_CONVERT")
    or shutil.which("ebook-convert")
    or r"C:\Program Files\Calibre2\ebook-convert.exe"
)

# ---------------------------------------------------------------- trim sizes
# width x height in inches, plus the margins for that size in points.
# Margins are asymmetric in the *gutter* sense: `inner` is the binding
# edge. See the note on mirroring in apply_margins() — calibre cannot
# mirror per page, so `inner` is applied to both sides and the value is
# chosen to be safe as a gutter on either edge.
# The horizontal margins are set by the verse, not by taste: this is a
# line-for-line edition, so a verse that turns over stops looking like one
# line and the whole point of the layout is lost. The poem's verses run to
# 90 characters (median 53, p99 73), and the measure has to hold nearly all
# of them. At the 6x9 values below the block is 4.18in and ~1.3% of the
# 12,107 verses turn over; widening further would buy little and start to
# look ungainly. tools/check_print.py re-measures the real rate.
TRIMS = {
    "6x9":     dict(w=6.0,  h=9.0,   inner=56, outer=38, top=58, bottom=64),
    "5.5x8.5": dict(w=5.5,  h=8.5,   inner=54, outer=38, top=54, bottom=60),
    "a5":      dict(w=5.83, h=8.27,  inner=56, outer=40, top=54, bottom=60),
}

# calibre's margin handling in the epub->pdf path, established by measuring
# the rendered output rather than from the docs. All of this is behaviour of
# the renderer, not of the stylesheet, and it is version-sensitive:
# tools/check_print.py re-measures it and fails the build if it drifts.
#
#   * --pdf-page-margin-* set an OUTER page box added on top of the content
#     margins (72pt each by default). The builder zeroes them so the content
#     margins alone determine the layout.
#   * every --margin-* value renders at DOUBLE its stated size, so each is
#     halved on the way in. Measured with the real build configuration
#     (running head and folio enabled, which is how this book is always
#     built):
#         --margin-right 24 -> 48pt   30 -> 60pt   42 -> 84pt   60 -> 120pt
#         --margin-top    58 -> 26pt(*)  90 -> 43pt(*)
#     (*) the vertical pair is measured to the BODY text, and the running
#     head and folio are laid inside the margin, so the body clearance is
#     the margin minus the head. The top/bottom values in TRIMS are the
#     body clearance wanted, and HEAD_ALLOWANCE_PT adds the head back.
#   * the rendered left margin also carries the verse number hang (~31pt at
#     this body size), which lives inside the text block, not the margin.
CALIBRE_MARGIN_FACTOR = 2

# Vertical space the running head / folio occupy inside the top and bottom
# margins: their own height plus HEAD_PAD_PT of clearance from the trim.
# Added to the requested body clearance so the head sits in the margin
# rather than eating into the text block. Measured: with 22pt reserved the
# body sat 39pt from the trim against a 58pt design, i.e. 19pt short.
HEAD_ALLOWANCE_PT = 60

# How far the head and folio are padded away from the page edge. calibre
# puts them flush against it otherwise, which is inside a printer's trim
# tolerance. 24pt (1/3 in) clears it with room to spare.
HEAD_PAD_PT = 24


# The body size of the printed edition, in points: the size the verse
# actually measures on the finished page. print.css carries no absolute
# body size (calibre's renderer ignores it) and sizes everything in em
# relative to this.
BODY_PT = 10.5

# calibre's PDF renderer does not render --pdf-default-font-size at face
# value: it applies a constant 0.75, measured across 12/13/14pt on the real
# multi-book build. So the requested size is the design size divided by
# that factor, and since the flag takes an INTEGER only sizes that are a
# multiple of 0.75 are reachable — which is why the body is 10.5pt (14 x
# 0.75) and not 10. tools/check_print.py re-measures this and fails if it
# drifts.
#
# Do not calibrate this against a single-book proof: calibre also applies a
# length-dependent rescale, so a one-book build reports ~0.844 and the full
# 24-book build silently comes out a tenth smaller everywhere.
CALIBRE_FONT_SCALE = 0.75
BASE_FONT_REQUEST = round(BODY_PT / CALIBRE_FONT_SCALE)   # 10.5pt -> 14

# Number every Nth verse line in the printed margin.
NUMBER_EVERY = 5

VERSE_RE = re.compile(r"^(\d+)(\s+)(.*)$")
DEF_RE = re.compile(r"^\[\^L(\d+)\]:\s*(.*)$")
REF_RE = re.compile(r"\[\^L(\d+)\]")


# Characters the source uses that the subsetted Gentium does not carry.
# Left alone they fall back to a sans face — Arial in the middle of a line
# of polytonic Greek — so each is mapped to a glyph the font does have.
# These are not compromises: the koronis is the correct character for an
# elision mark in Greek, and the arrow is only ever a "leads to" between
# line citations, which an en dash says as well on paper.
GLYPH_SUBSTITUTIONS = {
    "ʼ": "᾽",   # MODIFIER LETTER APOSTROPHE -> GREEK KORONIS
    "→": "–",   # RIGHTWARDS ARROW -> EN DASH
    "≈": "c. ",  # ALMOST EQUAL TO -> "c." (circa)
}


def substitute_glyphs(text: str) -> str:
    for src, dst in GLYPH_SUBSTITUTIONS.items():
        text = text.replace(src, dst)
    return text


def md_inline(text: str) -> str:
    """Convert the inline markdown used in the notes to HTML.

    The apparatus uses *italic*, **bold**, `code`, and [text](url) links.
    Escapes first, then re-introduces the tags, so stray < or & in the
    Greek or the prose cannot inject markup.
    """
    out = html.escape(text, quote=False)
    # Links: [label](href) -> label (print drops the URL, keeps the text)
    # unless the URL carries information the reader needs on paper, in
    # which case it is spelled out after the label.
    def _link(m: re.Match) -> str:
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://")):
            return f"{label} &lt;{href}&gt;"
        return label
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return out


def parse_book(text: str) -> tuple[str, str, list, dict]:
    """Split a book's markdown into (title, argument, body, notes).

    body is a list of ("verse", num, html) and ("break",) items.
    notes maps line-number -> note text (markdown).
    """
    lines = text.splitlines()
    title = ""
    argument = ""
    body: list = []
    notes: dict[str, str] = {}

    in_notes = False
    i = 0
    # Title (# Odyssey — Book N) and the italic argument beneath it.
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            title = ln[2:].strip()
            i += 1
            continue
        if ln.startswith("## Notes"):
            break
        if ln.strip().startswith("*") and ln.strip().endswith("*") and not argument:
            argument = ln.strip().strip("*").strip()
            i += 1
            continue
        if ln.strip() == "":
            i += 1
            continue
        break

    cur_note_key: str | None = None
    for ln in lines[i:]:
        if ln.startswith("## Notes"):
            in_notes = True
            cur_note_key = None
            continue

        if not in_notes:
            m = VERSE_RE.match(ln)
            if m:
                num, _, verse = m.groups()
                body.append(("verse", num, verse))
            elif ln.strip() == "":
                if body and body[-1][0] != "break":
                    body.append(("break",))
            continue

        # --- inside the notes section ---
        m = DEF_RE.match(ln)
        if m:
            cur_note_key = m.group(1)
            notes[cur_note_key] = m.group(2)
        elif cur_note_key and ln.strip():
            # continuation line of a multi-line note
            notes[cur_note_key] += " " + ln.strip()
        elif not ln.strip():
            cur_note_key = None

    return title, argument, body, notes


def render_verse(num: str, verse: str, note_order: dict) -> str:
    """One verse line: hanging number (every Nth), markers, turnover indent."""
    # Replace footnote refs with printed superscript numerals. The numeral
    # is the note's sequence within its book, so the reader looks up "12"
    # in the book's endnotes rather than a line number that may repeat.
    def _ref(m: re.Match) -> str:
        key = m.group(1)
        seq = note_order.get(key)
        if seq is None:
            return ""
        return f'<sup class="nm">{seq}</sup>'

    text = REF_RE.sub(_ref, verse)
    text = md_inline_verse(text)

    n = int(num)
    shown = str(n) if (n % NUMBER_EVERY == 0) else ""
    return f'<p class="v"><span class="ln">{shown}</span>{text}</p>'


def md_inline_verse(text: str) -> str:
    """Inline markdown inside a verse line.

    Same as md_inline but must not disturb the <sup> markers already
    inserted, so it escapes only the bare text segments.
    """
    parts = re.split(r"(<sup class=\"nm\">\d+</sup>)", text)
    out = []
    for p in parts:
        if p.startswith("<sup"):
            out.append(p)
        else:
            seg = html.escape(p, quote=False)
            seg = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", seg)
            seg = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", seg)
            out.append(seg)
    return "".join(out)


def render_book(n: int, text: str) -> str:
    title, argument, body, notes = parse_book(text)

    # Number the notes in the order their markers appear in the verse, so
    # the printed superscripts run 1..N through the book.
    note_order: dict[str, int] = {}
    seq = 0
    for item in body:
        if item[0] != "verse":
            continue
        for key in REF_RE.findall(item[2]):
            if key not in note_order:
                seq += 1
                note_order[key] = seq

    parts: list[str] = []
    # Book opener. The h1 text drives the running head via _SECTION_.
    parts.append(f"<h1>{html.escape(title)}</h1>")
    if argument:
        parts.append(f'<p class="argument">{md_inline(argument)}</p>')

    open_stanza = False
    for item in body:
        if item[0] == "verse":
            if not open_stanza:
                parts.append('<div class="stanza">')
                open_stanza = True
            parts.append(render_verse(item[1], item[2], note_order))
        else:
            if open_stanza:
                parts.append("</div>")
                open_stanza = False
    if open_stanza:
        parts.append("</div>")

    # Endnotes for this book, in printed-numeral order.
    if note_order:
        parts.append(f'<h2 class="notes-head">Notes to {html.escape(title)}</h2>')
        inv = sorted(note_order.items(), key=lambda kv: kv[1])
        for key, s in inv:
            body_md = notes.get(key)
            if body_md is None:
                continue
            # Show both the printed numeral and the verse line it belongs
            # to: "12 (l. 337)" — the line number is how a reader cites it.
            parts.append(
                f'<p class="note"><span class="nl">{s}</span>'
                f'<em>l.&nbsp;{html.escape(key)}</em>&nbsp; {md_inline(body_md)}</p>'
            )

    return "\n".join(parts)


def contents_page(book_nums: list[int], arguments: dict[int, str],
                  folios: dict[int, int] | None,
                  back: list[tuple[str, int | None]] | None = None) -> str:
    """The table of contents.

    Each book is listed with its argument — the one-line summary that also
    stands under the book's title — and its printed folio. Folios are only
    known after a render, so the first pass is built with them absent: the
    leader dots and the layout are identical either way, and the page count
    therefore does not change when the numbers are filled in on the second
    pass. That is what makes the numbers correct rather than off by however
    many pages the contents itself occupies.
    """
    rows: list[str] = []
    for n in book_nums:
        arg = arguments.get(n, "")
        folio = folios.get(n) if folios else None
        rows.append(
            '<p class="toc-line">'
            f'<span class="toc-bk">Book {n}</span>'
            f'<span class="toc-arg">{md_inline(arg)}</span>'
            '<span class="toc-dots"></span>'
            f'<span class="toc-pg">{folio if folio else ""}</span>'
            "</p>"
        )
    for label, folio in (back or []):
        rows.append(
            '<p class="toc-line toc-back">'
            f'<span class="toc-bk">{html.escape(label)}</span>'
            '<span class="toc-arg"></span>'
            '<span class="toc-dots"></span>'
            f'<span class="toc-pg">{folio if folio else ""}</span>'
            "</p>"
        )
    return ('<h1 class="fm">Contents</h1>\n<div class="toc">\n'
            + "\n".join(rows) + "\n</div>")


def front_matter() -> list[tuple[str, str]]:
    """(filename, html) pairs for the front matter, in order."""
    title = (
        '<div class="titlepage">'
        '<p class="tp-title">The Odyssey</p>'
        '<p class="tp-sub">a line-for-line translation</p>'
        '<hr class="tp-rule"/>'
        '<p class="tp-role">from the Greek of</p>'
        '<p class="tp-name">Homer</p>'
        '<p class="tp-role">translated by</p>'
        '<p class="tp-name">Claude <span class="tp-small">(Fable 5)</span></p>'
        '<p class="tp-role">edited and produced by</p>'
        '<p class="tp-name">Chris Duffy</p>'
        "</div>"
    )

    copyright_html = (
        '<div class="copyright-page">'
        "<p>The English translation — the 12,107 verse lines — is dedicated "
        "to the public domain under Creative Commons CC0 1.0. No permission "
        "is needed to copy, adapt, perform, or reuse it, for any purpose, "
        "including commercially.</p>"
        "<p>The apparatus — the line notes, the front matter, and the index "
        "of names and places — is &#169; 2026 Chris Duffy, licensed "
        "Creative Commons CC BY 4.0.</p>"
        "<p>The Greek underlying this translation is A.&#160;T. Murray's text "
        "from the Loeb Classical Library edition (<em>Homer: The Odyssey</em>, "
        "Heinemann/Putnam, 1919), in the public domain, as digitized by the "
        "Perseus Digital Library and used under CC BY-SA.</p>"
        "<p>Polytonic Greek is set in Gentium Plus, used under the SIL Open "
        "Font License.</p>"
        "<p>The text of this edition, in digital form, is at "
        "theclaudyssey.com.</p>"
        "</div>"
    )

    epigraph = (
        '<div class="epigraph-page"><p class="epigraph">'
        '<span class="greek" lang="grc">'
        "&#7940;&#957;&#948;&#961;&#945; &#956;&#959;&#953; &#7956;&#957;&#957;"
        "&#949;&#960;&#949;, &#956;&#959;&#8166;&#963;&#945;, &#960;&#959;"
        "&#955;&#973;&#964;&#961;&#959;&#960;&#959;&#957;"
        "</span>"
        "Tell me the man, Muse &#8212; the man of many turnings"
        "</p></div>"
    )

    note = (
        '<h1 class="fm">A Note on the Text</h1>'
        '<p class="fm">The Greek is A.&#160;T. Murray\'s text from the Loeb '
        "Classical Library edition of 1919, as digitized by the Perseus "
        "Digital Library from the polytonic vulgate. The English translation "
        "is original to this project; each of the 12,107 English lines is "
        "keyed one-to-one to its Greek line, so a citation to the Greek finds "
        "the same line here.</p>"
        '<p class="fm">Line numbers are printed in the margin every fifth '
        "line. Where a verse runs past the measure of the page, the "
        "continuation is indented, so an indented line is always the tail of "
        "the verse above it and never a new verse.</p>"
        '<p class="fm">The scholarly apparatus &#8212; 1,260 notes across the '
        "poem &#8212; is printed as endnotes at the close of each book. A "
        "raised numeral in the verse marks a note; the notes are numbered "
        "through each book, and each note also gives the line it belongs to "
        "(<em>l.&#160;337</em>), which is how it should be cited.</p>"
        '<p class="fm">Two quirks of Murray\'s text are kept faithfully. '
        "Lines 3.304&#8211;305 and 14.63&#8211;64 are printed in the "
        "transposed order he gives them, with the traditional numbering "
        "retained. Lines 10.456, 16.101, and 23.49, which he athetizes as "
        "interpolations, are absent, and the numbering skips them.</p>"
    )

    return [
        ("00-title.html", title),
        ("01-copyright.html", copyright_html),
        ("02-epigraph.html", epigraph),
        ("03-note.html", note),
    ]


CITE_RE = re.compile(r"\b([12]?\d)\.(\d{1,3})(–\d{1,3}|ff)?")


def index_html(present: set[int],
               guides: dict[str, str] | None = None) -> str:
    """The index of names as print back matter.

    The EPUB turns every book.line citation into a link. On paper a link
    is meaningless, so the citations are left as printed references — the
    reader turns to the line. Everything else is carried over.

    Each line of an entry is classed by what it is (headword, description,
    references, cross-references) so the stylesheet can size the headword
    above the apparatus lines beneath it.

    `guides` maps a headword to the guide words of the page that entry
    opens ("Achaea – Aeetes"). The marker is written as a zero-size span at
    the start of that entry's headword line; calibre's chapter detection
    picks the span up as a section and its text becomes that page's
    running head (see the --chapter option in build()). The mapping comes
    from measuring a rendered copy: which entries share a page is not
    knowable before the book is paginated.
    """
    src = ROOT / "index" / "index.md"
    if not src.exists():
        return ""
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"^# .*\n", "", text, count=1)
    text = re.sub(r"^\s*Every named person.*?pronunciation scheme\.\s*\n",
                  "", text, count=1, flags=re.S)

    out = [
        '<h1 class="fm">Index of Names and Places</h1>',
        '<p class="fm">Every named person, god, people, and place in the '
        "poem, with a pronunciation (<em>Say:</em>), epithets, aliases, kin, "
        "and line citations. Pronunciations give the traditional anglicized "
        "reading; stress falls on the capitalized syllable.</p>",
        '<div class="name-index">',
    ]
    guides = guides or {}
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s == "---":
            continue
        m = HEADWORD_RE.match(s)
        if m:
            guide = guides.get(m.group(1))
            marker = (f'<span class="guide">{html.escape(guide)}</span>'
                      if guide else "")
            out.append(f'<p class="hw">{marker}{md_inline(s)}</p>')
            continue
        if s.startswith("**Refs:**"):
            cls = "refs"
        elif s.startswith("*See also:*"):
            cls = "xref"
        elif s.startswith("*"):
            cls = "meta"          # Epithets, Also called, Kin
        else:
            cls = "desc"
        out.append(f'<p class="{cls}">{md_inline(s)}</p>')
    out.append("</div>")
    return "\n".join(out)


# A headword line: "**Achaea** (Ἀχαΐα) · PLACE — ..." or "**Apeire** · PLACE".
# "**Refs:**" lines are bold too, hence the lookahead.
HEADWORD_RE = re.compile(r"^\*\*(?!Refs:)([^*]+)\*\*\s+[(·]")

GUIDE_SEP = " – "


def _index_headwords() -> list[str]:
    """The index's headwords, in the order they are printed."""
    src = ROOT / "index" / "index.md"
    if not src.exists():
        return []
    out = []
    for ln in src.read_text(encoding="utf-8").splitlines():
        m = HEADWORD_RE.match(ln.strip())
        if m:
            out.append(m.group(1))
    return out


def _index_guides(pdf_path: Path, headwords: list[str]) -> dict[str, str]:
    """Guide words for the index pages, measured from the rendered PDF.

    Returns {first headword beginning on the page: "First – Last"} for
    every index page after the first. The first page keeps the index title
    as its head, as a chapter opener does. A page on which no entry begins
    (one entry filling the page) gets no marker of its own and inherits
    the previous page's head; none of the entries is that long, and it is
    reported if one ever is.

    The headwords are matched in printed order against the start of the
    extracted lines, with the "(" or "·" that follows every headword as
    the guard against a description line that happens to open with a name.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return {}
    start = _index_page(pdf_path)
    if not start:
        return {}
    reader = PdfReader(str(pdf_path))
    guides: dict[str, str] = {}
    pos = 0
    orphan_pages = 0
    for i in range(start - 1, len(reader.pages)):
        text = reader.pages[i].extract_text() or ""
        found: list[str] = []
        for ln in text.split("\n"):
            if pos >= len(headwords):
                break
            if re.match(re.escape(headwords[pos]) + r"\s+[(·]", ln.strip()):
                found.append(headwords[pos])
                pos += 1
        if i == start - 1:
            continue
        if not found:
            orphan_pages += 1
            continue
        first, last = found[0], found[-1]
        guides[first] = (first if first == last
                         else f"{first}{GUIDE_SEP}{last}")
    if pos != len(headwords):
        print(f"  WARNING: index guide words: matched {pos} of "
              f"{len(headwords)} headwords in the rendered index; the "
              "guide words after the last match will be wrong")
    if orphan_pages:
        print(f"  WARNING: {orphan_pages} index page(s) on which no entry "
              "begins carry the previous page's guide words")
    return guides


def _strip_outline(pdf_path: Path, titles: set[str]) -> int:
    """Drop the outline (bookmark) entries whose title is in `titles`.

    The guide-word markers reach the running head by way of calibre's TOC,
    and calibre also writes the TOC into the PDF's outline; seventy
    bookmarks reading "Achaea – Aeetes" are not wanted there. The outline
    is a doubly linked list under /Outlines; the unwanted items are
    unlinked in place.
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, NumberObject
    except ImportError:
        return 0
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter(clone_from=reader)
    root = writer._root_object
    if "/Outlines" not in root:
        return 0
    outlines = root["/Outlines"].get_object()
    removed = 0
    node = outlines.get("/First")
    while node is not None:
        item = node.get_object()
        nxt = item.get("/Next")
        if str(item.get("/Title", "")) in titles:
            prev = item.get("/Prev")
            if prev is not None:
                pv = prev.get_object()
                if nxt is not None:
                    pv[NameObject("/Next")] = nxt
                else:
                    del pv["/Next"]
            elif nxt is not None:
                outlines[NameObject("/First")] = nxt
            else:
                del outlines["/First"]
            if nxt is not None:
                nx = nxt.get_object()
                if prev is not None:
                    nx[NameObject("/Prev")] = prev
                else:
                    del nx["/Prev"]
            elif prev is not None:
                outlines[NameObject("/Last")] = prev
            else:
                del outlines["/Last"]
            removed += 1
        node = nxt
    if removed:
        count = int(outlines.get("/Count", 0))
        if count > 0:
            outlines[NameObject("/Count")] = NumberObject(count - removed)
        with open(pdf_path, "wb") as fh:
            writer.write(fh)
    return removed


def page_html(title: str, body: str) -> str:
    # Every section passes through here, so this is the one place the glyph
    # substitution has to be applied.
    return (
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml"><head>'
        '<meta charset="utf-8"/>'
        f"<title>{html.escape(title)}</title>"
        '<link rel="stylesheet" type="text/css" href="print.css"/>'
        f"</head><body>{substitute_glyphs(body)}</body></html>\n"
    )


def _book_opener_pages(pdf_path: Path) -> dict[int, int]:
    """Which 1-based page does each book open on?

    Reads the finished PDF and finds the pages carrying a book opener (the
    display title "Odyssey — Book n", which appears only on the opener).
    Used by the recto pass, which cannot know page positions until the book
    has been rendered once.
    """
    # pypdf rather than pdfplumber: this runs once per recto pass over the
    # whole book, and pdfplumber's layout analysis makes that minutes rather
    # than seconds. Plain text extraction is all that is needed here.
    try:
        from pypdf import PdfReader
    except ImportError:
        return {}
    found: dict[int, int] = {}
    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # skip the running head (first line) and look at the body
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for ln in lines[1:3]:
            m = re.match(r"Odyssey\s*[—–-]\s*Book\s+(\d+)\s*$", ln)
            if m:
                found.setdefault(int(m.group(1)), i)
                break
    return found


def _index_page(pdf_path: Path) -> int | None:
    """1-based page the index of names starts on, for the contents entry."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    for i, page in enumerate(PdfReader(str(pdf_path)).pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        for ln in [x.strip() for x in text.split("\n") if x.strip()][:3]:
            if re.match(r"INDEX OF NAMES AND PLACES\s*$", ln, re.I):
                return i
    return None


def _find_blank_leaves(pdf_path: Path) -> set[int]:
    """0-based indices of the blank leaves inserted by the recto pass.

    They are the pages whose only text is the running head and folio:
    all-uppercase (the head is set in caps, verse and notes are not) and
    very little of it.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return set()
    out: set[int] = set()
    for i, page in enumerate(PdfReader(str(pdf_path)).pages):
        text = (page.extract_text() or "").strip()
        letters = [c for c in text if c.isalpha()]
        if letters and all(c.isupper() for c in letters) and len(text) < 80:
            out.add(i)
    return out


def _clear_running_heads(pdf_path: Path, pages: set[int]) -> int:
    """Remove the running head and folio from the given 0-based pages.

    calibre draws the head and folio into a per-page Form XObject
    (/HeaderFooterNNN) that the page's content stream invokes with `Do`.
    Because each page gets its OWN xobject, emptying one clears that page's
    head and folio and nothing else — the body content lives in a separate
    stream and is untouched.

    Used for the front matter, where a folio should not print at all
    (--pdf-page-number-map maps those pages to 0, but calibre then draws a
    literal "0" rather than omitting it), and for the blank leaves inserted
    by the recto pass.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return 0

    reader = PdfReader(str(pdf_path))
    cleared = 0
    for i, page in enumerate(reader.pages):
        if i not in pages:
            continue
        res = page.get("/Resources")
        xo = res.get_object().get("/XObject") if res else None
        if not xo:
            continue
        hit = False
        for name, ref in xo.get_object().items():
            if not str(name).startswith("/HeaderFooter"):
                continue
            stream = ref.get_object()
            stream.set_data(b"")          # draw nothing
            hit = True
        if hit:
            cleared += 1

    if cleared:
        writer = PdfWriter(clone_from=reader)
        with open(pdf_path, "wb") as fh:
            writer.write(fh)
    return cleared


def build(book_nums: list[int], trim: str, force_recto: bool,
          odd_even_offset: int | None) -> Path:
    if trim not in TRIMS:
        sys.exit(f"unknown trim {trim!r}; choose from {', '.join(TRIMS)}")
    geo = TRIMS[trim]

    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "fonts").mkdir(parents=True)
    for f in ["Gentium-Regular.woff2", "Gentium-Italic.woff2"]:
        shutil.copy(EPUB_ASSETS / f, WORK / "fonts" / f)
    shutil.copy(BUILD / "print.css", WORK / "print.css")

    # One concatenated HTML document. Calibre's html input follows links
    # from a single root file; passing sibling files individually silently
    # drops all but the first. Concatenating also lets the builder control
    # recto-forcing directly, by inserting blank pages between sections.
    front = [body for _name, body in front_matter()]
    books: dict[int, str] = {}
    arguments: dict[int, str] = {}
    for n in book_nums:
        src = SRC / f"book-{n:02d}.md"
        if not src.exists():
            sys.exit(f"missing {src}")
        text = src.read_text(encoding="utf-8")
        books[n] = render_book(n, text)
        arguments[n] = parse_book(text)[1]
    idx = index_html(set(book_nums))

    # Folios for the contents, filled in on the second pass (see the
    # contents-page docstring). None on the first pass.
    toc_folios: dict[int, int] | None = None
    toc_back: list[tuple[str, int | None]] = []

    # A blank page that actually holds. Three things are load-bearing:
    #   * an explicit height, or the element collapses and no page appears;
    #   * a child with real content (&#160;), same reason;
    #   * INLINE styles. calibre rewrites class-based rules into its own
    #     generated classes during the html->epub step and drops the height
    #     in the process, so a stylesheet rule silently stops working.
    # Only page-break-BEFORE is set: the book's own h1 supplies the break
    # after. Setting both produces two blank pages, not one.
    # The page ends up with no body text — only the running head and folio,
    # which are stripped afterwards by _blank_the_pages().
    BLANK = (
        '<div style="page-break-before:always;height:7in">'
        '<p style="height:6in;margin:0">&#160;</p></div>'
    )

    def assemble(blank_before: set[int]) -> str:
        parts = list(front)
        parts.append(contents_page(book_nums, arguments, toc_folios,
                                   toc_back))
        for n in book_nums:
            if n in blank_before:
                parts.append(BLANK)
            parts.append(books[n])
        if idx:
            parts.append(idx)
        return "\n".join(parts)

    root = WORK / "odyssey-print.html"
    root.write_text(page_html("The Odyssey", assemble(set())),
                    encoding="utf-8")

    # --- html -> epub. The epub intermediate is what preserves chapter
    # boundaries for the running heads (_SECTION_ tracks the h1).
    epub = WORK / "print-src.epub"

    def to_epub() -> None:
        subprocess.run(
            [EBOOK_CONVERT, str(root), str(epub),
             "--title", "The Odyssey",
             "--authors", "Homer",
             "--language", "en",
             "--disable-font-rescaling",
             "--change-justification", "left",
             # h1 for the running heads; the guide spans in the index give
             # each index page its own head (see index_html)
             "--chapter", "//h:h1 | //h:span[@class='guide']",
             "--chapter-mark", "none",
             "--no-default-epub-cover",
             "--dont-split-on-page-breaks"],
            check=True, cwd=WORK, stdout=subprocess.DEVNULL)

    print("building intermediate epub...")
    to_epub()

    # --- epub -> pdf
    suffix = trim.replace(".", "-")
    out = BUILD / (f"odyssey-print-{suffix}.pdf" if book_nums != [1]
                   else f"odyssey-print-{suffix}-book01.pdf")

    # Running head and folio. calibre replaces _SECTION_ with the current
    # chapter (the h1) and _PAGENUM_ with the folio.
    # The template's root element must be a <header>/<footer>, which calibre
    # lays out as a flex row spanning the page; a bare <div> root is treated
    # as a flex item that shrinks to its content and sits at flex-start, so
    # width:100% and text-align do nothing and everything lands hard left.
    # Children are positioned with flex margins (margin:auto centers), and
    # calibre's own even-page/odd-page classes show a child only on that
    # page parity — which is what mirrors the folio to the outside edge:
    # bottom-left on a verso (even), bottom-right on a recto (odd).
    # The head and folio are placed by calibre hard against the top and
    # bottom of the page box, which on a 6x9 leaves them ~16pt from the
    # trim — inside the +/-3mm (8.5pt) trim tolerance a printer works to,
    # so a bad cut would clip them. The padding pushes them into the
    # margin proper; HEAD_ALLOWANCE_PT reserves the room for it.
    header = (
        '<header style="font-family:Georgia,serif;font-size:8pt;'
        'letter-spacing:0.08em;box-sizing:border-box;'
        f'padding:{HEAD_PAD_PT}pt 0.3in 0;'
        'text-transform:uppercase">'
        '<div style="margin:auto">_SECTION_</div>'
        '</header>'
    )
    footer = (
        '<footer style="font-family:Georgia,serif;font-size:9pt;'
        'box-sizing:border-box;'
        f'padding:0 0.3in {HEAD_PAD_PT}pt">'
        '<div class="even-page">_PAGENUM_</div>'
        '<div class="odd-page" style="margin-left:auto">_PAGENUM_</div>'
        '</footer>'
    )


    # See the CALIBRE_* notes above. Every margin renders at 2x its stated
    # value, so halve. The vertical pair also has to carry the running head
    # and the folio, which sit inside the margin.
    f = CALIBRE_MARGIN_FACTOR
    ml = geo["inner"] / f
    mr = geo["outer"] / f
    mt = (geo["top"] + HEAD_ALLOWANCE_PT) / f
    mb = (geo["bottom"] + HEAD_ALLOWANCE_PT) / f

    # Front matter carries no visible folio — a title page with a printed
    # "1" on it is wrong — and the folios count from the poem's first page,
    # which is the convention. --pdf-page-number-map takes a JavaScript
    # expression over the physical page number n, and calibre prints nothing
    # when it evaluates to 0. How many pages the front matter actually
    # occupies is only known once rendered, so this starts as a no-op and is
    # set from the measured position of Book 1 below.
    page_map: list[str] = []

    cmd_pdf = [
        EBOOK_CONVERT, str(epub), str(out),
        "--custom-size", f'{geo["w"]}x{geo["h"]}',
        "--unit", "inch",
        "--margin-left", str(ml),
        "--margin-right", str(mr),
        "--margin-top", str(mt),
        "--margin-bottom", str(mb),
        # zero the outer page box; the content margins above are the design
        "--pdf-page-margin-left", "0",
        "--pdf-page-margin-right", "0",
        "--pdf-page-margin-top", "0",
        "--pdf-page-margin-bottom", "0",
        "--pdf-page-numbers",
        "--pdf-header-template", header,
        "--pdf-footer-template", footer,
        "--pdf-serif-family", "Gentium",
        "--pdf-standard-font", "serif",
        # calibre imposes its own base font size on the PDF renderer and
        # ignores the stylesheet's body size; left at the default it renders
        # the verse at ~17pt, which wraps every line and triples the page
        # count. See BASE_FONT_REQUEST for the scale compensation.
        "--pdf-default-font-size", str(BASE_FONT_REQUEST),
        # Without this calibre also rescales by a factor that depends on the
        # document's length, so the edition's type size would depend on how
        # many books are in the build.
        "--disable-font-rescaling",
        "--embed-all-fonts",
        "--subset-embedded-fonts",
    ]
    if odd_even_offset:
        # CropBox-based mirroring. Not all print shops honor the CropBox,
        # so this is opt-in and the base margins are already gutter-safe.
        cmd_pdf += ["--pdf-odd-even-offset", str(odd_even_offset)]

    def to_pdf() -> None:
        subprocess.run(cmd_pdf + page_map, check=True, cwd=WORK,
                       stdout=subprocess.DEVNULL)

    print(f"rendering pdf ({trim}, {geo['w']}x{geo['h']}in)...")
    to_pdf()

    # --- recto pass.
    # Book openers belong on a right-hand (odd) page. Neither `break-before:
    # recto` nor @page :left/:right survives calibre's renderer, so where a
    # book lands can only be discovered by rendering and measuring.
    blanks: set[int] = set()
    if force_recto and len(book_nums) > 1:
        # Fix the books one at a time, earliest first, and never take a
        # blank back. Adding a blank shifts everything after it, so a book
        # that looked fine can be pushed onto a verso — but a book EARLIER
        # than the one just fixed can never move. Each pass therefore
        # settles at least one more book permanently, and the whole thing
        # terminates in at most one pass per book.
        #
        # (Toggling blanks on and off instead — reconsidering every book
        # each pass — oscillates and does not converge: two books trade
        # places indefinitely.)
        for attempt in range(1, len(book_nums) + 2):
            openers = _book_opener_pages(out)
            if not openers:
                print("recto pass: could not locate book openers "
                      "(pypdf missing?); skipping")
                break
            offenders = [n for n in book_nums
                         if openers.get(n) and openers[n] % 2 == 0]
            if not offenders:
                if attempt == 1:
                    print("recto pass: every book already opens on a recto")
                else:
                    print(f"recto pass: all books on a recto after "
                          f"{attempt - 1} pass(es), {len(blanks)} blank(s)")
                break
            # fix only the first unfixed offender; later ones will move
            nxt = next((n for n in offenders if n not in blanks), None)
            if nxt is None:
                print(f"recto pass: cannot place {len(offenders)} book(s) "
                      f"on a recto: {', '.join(map(str, offenders))}")
                break
            blanks.add(nxt)
            print(f"recto pass {attempt}: book {nxt} opens on a verso "
                  f"({len(offenders)} left); inserting blank "
                  f"({len(blanks)} total)")
            root.write_text(page_html("The Odyssey", assemble(blanks)),
                            encoding="utf-8")
            to_epub()
            to_pdf()

    # --- folios.
    # Suppress the folio on the front matter and count page 1 from the
    # poem's first page. How many pages the front matter occupies is only
    # known once rendered, so it is measured here and the book re-rendered
    # with the map. This must happen before the blanking pass below, which
    # edits the finished PDF and would be undone by another render.
    openers = _book_opener_pages(out)
    first = openers.get(min(book_nums)) if openers else None
    n_front = (first - 1) if first and first > 1 else 0
    if n_front:
        page_map[:] = ["--pdf-page-number-map",
                       f"if (n <= {n_front}) 0; else n - {n_front};"]
        print(f"folios: {n_front} front-matter page(s) unnumbered; "
              "page 1 is the poem's first page")
        to_pdf()

    # --- contents.
    # The folios are only knowable once the book has been paginated, so the
    # contents has been standing empty until now. Fill it and render again.
    # The filled page is the same size as the empty one — same rows, same
    # leaders, only the numerals differ — so nothing moves and the numbers
    # stay true. Verified below rather than assumed.
    openers = _book_opener_pages(out)
    if openers:
        toc_folios = {n: p - n_front for n, p in openers.items()
                      if p - n_front > 0}
        idx_page = _index_page(out)
        toc_back = ([("Index of Names and Places", idx_page - n_front)]
                    if idx_page and idx_page - n_front > 0 else [])
        print(f"contents: filling {len(toc_folios)} page number(s)")
        root.write_text(page_html("The Odyssey", assemble(blanks)),
                        encoding="utf-8")
        to_epub()
        to_pdf()

        # If filling the numbers changed the pagination, every number on
        # the page is now wrong. Say so rather than shipping it quietly.
        after = _book_opener_pages(out)
        moved = [n for n in openers
                 if after.get(n) is not None and after[n] != openers[n]]
        if moved:
            print(f"  WARNING: {len(moved)} book(s) shifted when the "
                  "contents was filled; the printed page numbers are wrong. "
                  "Check tools/check_print.py before using this file.")
        elif len(after) != len(openers):
            print("  WARNING: the book count changed on the contents pass")

    # --- index guide words.
    # The running head on each index page names the first and last entry
    # beginning on it, as a dictionary does. Which entries share a page is
    # only known once the book is paginated, so the finished layout is
    # measured and the markers written in. They are zero-size spans, so
    # nothing should move; that is verified by measuring again, and the
    # pass repeats from the new measurement if it did.
    guide_titles: set[str] = set()
    headwords = _index_headwords() if idx else []
    if headwords:
        guides = _index_guides(out, headwords)
        openers_before = _book_opener_pages(out)
        for attempt in range(1, 4):
            if not guides:
                break
            idx = index_html(set(book_nums), guides)
            root.write_text(page_html("The Odyssey", assemble(blanks)),
                            encoding="utf-8")
            to_epub()
            to_pdf()
            again = _index_guides(out, headwords)
            if again == guides:
                print(f"index guide words: {len(guides)} page(s)")
                guide_titles = set(guides.values())
                break
            print(f"index guide words: pagination shifted on pass "
                  f"{attempt}; re-measuring")
            guides = again
        else:
            print("  WARNING: index guide words did not settle in 3 passes")
        if _book_opener_pages(out) != openers_before:
            print("  WARNING: the books shifted when the guide words were "
                  "added; the contents page numbers are wrong. Check "
                  "tools/check_print.py before using this file.")

    # --- final pass over the finished file.
    # Clear the head and folio from the front matter (calibre draws a
    # literal "0" there rather than omitting the folio) and from the blank
    # leaves the recto pass inserted. Both are done in one rewrite.
    strip: set[int] = set(range(n_front))
    blanks_found = _find_blank_leaves(out)
    strip |= blanks_found
    if strip:
        cleared = _clear_running_heads(out, strip)
        if cleared:
            print(f"cleared the running head and folio from {cleared} page(s)"
                  f" ({len(blanks_found)} blank leaf/leaves, "
                  f"{len(strip) - len(blanks_found)} front matter)")

    if guide_titles:
        n = _strip_outline(out, guide_titles)
        if n:
            print(f"dropped {n} guide-word entries from the pdf outline")

    print(f"\nwrote {out}  ({out.stat().st_size:,} bytes)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", nargs="*", type=int,
                    help="book numbers to include (default: all 24)")
    ap.add_argument("--trim", default="6x9", choices=sorted(TRIMS),
                    help="trim size (default: 6x9 US trade)")
    ap.add_argument("--no-recto", action="store_true",
                    help="do not force book openers onto a recto page")
    ap.add_argument("--odd-even-offset", type=int, default=None,
                    help="shift text by N pt for gutter (CropBox; opt-in)")
    args = ap.parse_args()
    nums = args.books if args.books else list(range(1, 25))
    build(nums, args.trim, not args.no_recto, args.odd_even_offset)
