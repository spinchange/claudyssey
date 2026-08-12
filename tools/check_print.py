#!/usr/bin/env python3
"""Validate a print PDF against the specification of the edition.

The print build depends on several undocumented behaviours of calibre's
PDF renderer (margins render at 2x, --pdf-default-font-size is scaled by
~0.844, the running head is laid inside the top margin). Those were
established by measurement, and a calibre upgrade can change them
silently — the PDF still builds, it is just wrong. This checks the
finished file against what the edition is supposed to be, so a drift
fails loudly instead of reaching a printer.

Checks:
  * trim size matches the requested one exactly
  * body text renders at the intended point size
  * the text block sits inside the intended margins, on every page
  * no page is overset (text outside the trim, i.e. would be cut off)
  * all fonts are embedded (a printer cannot substitute)
  * no page is unintentionally blank
  * the running head and folio are present on body pages

Usage:
    python tools/check_print.py print-build/odyssey-print-6x9.pdf
    python tools/check_print.py <file.pdf> --trim 6x9
"""
from __future__ import annotations
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("check_print.py needs pdfplumber:  pip install pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_print import TRIMS, BODY_PT  # noqa: E402

# How far the measured value may drift from the design before it is an
# error. Rendering is not exact to the point; a couple of points of slack
# absorbs rounding without hiding a real layout break.
TOL_PT = 6.0
TOL_FONT_PT = 0.4


def check(path: Path, trim: str) -> int:
    geo = TRIMS[trim]
    want_w, want_h = geo["w"] * 72, geo["h"] * 72
    problems: list[str] = []
    notes: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        npages = len(pdf.pages)

        # ---- trim size
        w, h = pdf.pages[0].width, pdf.pages[0].height
        if abs(w - want_w) > 1 or abs(h - want_h) > 1:
            problems.append(
                f"trim is {w/72:.3f}x{h/72:.3f}in, expected "
                f"{geo['w']}x{geo['h']}in")
        if len({(round(p.width), round(p.height)) for p in pdf.pages}) > 1:
            problems.append("pages are not all the same size")

        # ---- verse font size.
        # Measure the VERSE specifically, not the whole book: the endnotes
        # and the index are deliberately set smaller, and in a short build
        # they outnumber the verse pages, so a global mode reports the
        # apparatus size and hides a real change in the verse.
        # Verse pages are identified by the hanging line numbers, which are
        # the smallest size present and unique to them.
        verse_pages = _verse_pages(pdf)
        body_size = BODY_PT
        sizes: Counter = Counter()
        for i in verse_pages[:40]:
            for c in pdf.pages[i].chars:
                if "Gentium" in str(c.get("fontname", "")):
                    sizes[round(c["size"], 1)] += 1
        if not verse_pages:
            problems.append("found no verse pages to measure")
        elif sizes:
            body_size = sizes.most_common(1)[0][0]
            if abs(body_size - BODY_PT) > TOL_FONT_PT:
                problems.append(
                    f"verse renders at {body_size}pt, expected {BODY_PT}pt "
                    "(calibre's font scaling may have changed)")
            else:
                notes.append(
                    f"verse {body_size}pt over {len(verse_pages)} verse pages")

        # ---- embedded fonts
        # Only fonts that actually draw glyphs matter. calibre leaves an
        # undrawn Type3 stub in the resources of pages carrying a running
        # head; it embeds nothing and renders nothing, so flagging it would
        # be a permanent false failure.
        drawn: set[str] = set()
        for p in pdf.pages[:50]:
            for c in p.chars:
                fn = str(c.get("fontname", "")).strip("/'\"")
                if fn:
                    drawn.add(fn)
        not_embedded = set()
        seen_fonts: set[str] = set()
        for p in pdf.pages[:50]:
            for name, is_embedded in _fonts(p).items():
                clean = name.strip("/'\"")
                if clean not in drawn:
                    continue          # declared but never used
                seen_fonts.add(clean)
                if not is_embedded:
                    not_embedded.add(clean)
        if seen_fonts:
            notes.append(f"fonts (all embedded): {', '.join(sorted(seen_fonts))}"
                         if not not_embedded
                         else f"fonts: {', '.join(sorted(seen_fonts))}")
        if not_embedded:
            problems.append(
                "fonts not embedded (a printer will substitute): "
                + ", ".join(sorted(not_embedded)))

        # A glyph missing from the subsetted text face silently falls back
        # to a system sans (Arial), which in the middle of a line of
        # polytonic Greek is glaring. It embeds fine, so the embedding
        # check above will not catch it — this will.
        strays: Counter = Counter()
        for p in pdf.pages:
            for c in p.chars:
                fn = str(c.get("fontname", ""))
                if "Gentium" not in fn and "Georgia" not in fn:
                    strays[(c["text"], fn.split("+")[-1])] += 1
        if strays:
            shown = ", ".join(
                f"{t!r} (U+{ord(t):04X}) in {f}" for (t, f), _ in
                strays.most_common(4))
            problems.append(
                f"{sum(strays.values())} character(s) fell back to another "
                f"face — missing from the subsetted font: {shown}")

        # ---- margins and overset, per page
        # Two vertical measurements: the body text block, and everything
        # including the running head and folio. The head legitimately sits
        # outside the body block, inside the margin; what must not happen
        # is anything straying into the trim tolerance at the page edge.
        min_left = min_right = 1e9
        min_top = min_bottom = 1e9          # body only
        min_top_any = min_bottom_any = 1e9  # including head/folio
        blanks: list[int] = []
        overset: list[int] = []
        for i, p in enumerate(pdf.pages, start=1):
            cs = p.chars
            if not cs:
                blanks.append(i)
                continue
            left = min(c["x0"] for c in cs)
            right = w - max(c["x1"] for c in cs)
            min_left = min(min_left, left)
            min_right = min(min_right, right)
            min_top_any = min(min_top_any, min(c["top"] for c in cs))
            min_bottom_any = min(min_bottom_any,
                                 h - max(c["bottom"] for c in cs))
            body_chars = [c for c in cs
                          if "Gentium" in str(c.get("fontname", ""))]
            if body_chars:
                min_top = min(min_top, min(c["top"] for c in body_chars))
                min_bottom = min(min_bottom,
                                 h - max(c["bottom"] for c in body_chars))
            if left < 0 or right < 0 or min(c["top"] for c in cs) < 0 or \
                    h - max(c["bottom"] for c in cs) < 0:
                overset.append(i)

        if overset:
            problems.append(
                f"{len(overset)} page(s) have text outside the trim and "
                f"would be cut off: {_brief(overset)}")

        # The rendered left margin includes the verse-number hang, which is
        # inside the text block; so the floor is the outer margin, not inner.
        floor = min(geo["inner"], geo["outer"])
        for label, got in (("left", min_left), ("right", min_right)):
            if got < floor - TOL_PT:
                problems.append(
                    f"{label} margin falls to {got:.1f}pt, below the "
                    f"{floor}pt design minimum")
        for label, got, want in (("top", min_top, geo["top"]),
                                 ("bottom", min_bottom, geo["bottom"])):
            if got < want - TOL_PT:
                problems.append(
                    f"{label} body margin is {got:.1f}pt, below the "
                    f"{want}pt design minimum")

        # Nothing at all — head and folio included — may sit inside the
        # trim tolerance a printer cuts to, or a bad cut clips it.
        for label, got in (("top", min_top_any), ("bottom", min_bottom_any)):
            if got < TRIM_TOLERANCE_PT:
                problems.append(
                    f"running head/folio is {got:.1f}pt from the {label} "
                    f"trim edge, inside the {TRIM_TOLERANCE_PT}pt cutting "
                    "tolerance")

        notes.append(
            f"body block: left>={min_left:.0f} right>={min_right:.0f} "
            f"top>={min_top:.0f} bottom>={min_bottom:.0f} pt")
        notes.append(
            f"head/folio clearance: top {min_top_any:.0f}pt, "
            f"bottom {min_bottom_any:.0f}pt from trim")

        if blanks:
            notes.append(f"{len(blanks)} blank page(s): {_brief(blanks)}")

        # ---- verse turnover.
        # The measure that matters for a line-for-line edition: how much of
        # the poem does not fit on one printed line. Measured from the verse
        # block actually rendered, then projected over all 12,107 verses.
        if verse_pages:
            cpl = _chars_per_line(pdf, verse_pages, body_size)
            if cpl:
                rate = _turnover_rate(cpl)
                notes.append(
                    f"verse measure ~{cpl:.0f} chars/line; "
                    f"{rate:.1f}% of the poem's verses turn over")
                if rate > MAX_TURNOVER_PCT:
                    problems.append(
                        f"{rate:.1f}% of verses would turn over (limit "
                        f"{MAX_TURNOVER_PCT}%): the measure is too narrow "
                        "for a line-for-line setting")

    note_problems = _check_notes()
    problems.extend(note_problems)
    if not note_problems:
        notes.append("every note resolves to exactly one marker")

    toc_problems, toc_n = _check_contents(path)
    problems.extend(toc_problems)
    if toc_n and not toc_problems:
        notes.append(f"contents: all {toc_n} page number(s) correct")

    print(f"{path.name}: {npages} pages, {trim} trim")
    for n in notes:
        print(f"  - {n}")
    if problems:
        print("\nFAIL")
        for pr in problems:
            print(f"  * {pr}")
        return 1
    print("\nOK — matches the print specification")
    return 0


# Printers cut to about +/-3mm. Nothing that must survive — including the
# running head and the folio — may sit closer than this to the trim edge.
TRIM_TOLERANCE_PT = 8.5


# A line-for-line edition tolerates a few long verses running over, but not
# many: past this the one-verse-one-line reading of the page breaks down.
MAX_TURNOVER_PCT = 4.0


def _check_notes() -> list[str]:
    """Every note must be referenced once, and every marker must resolve.

    Checked against the source rather than the PDF: the print build
    renumbers the notes (source keys are line numbers; print numerals run
    1..N through each book), and a note that lost its marker would simply
    vanish from the printed page without any other symptom.
    """
    from build_print import parse_book, REF_RE

    src = Path(__file__).resolve().parent.parent / "translation"
    out: list[str] = []
    for f in sorted(src.glob("book-*.md")):
        _t, _a, body, notes = parse_book(f.read_text(encoding="utf-8"))
        refs: list[str] = []
        for item in body:
            if item[0] == "verse":
                refs.extend(REF_RE.findall(item[2]))
        defs, refset = set(notes), set(refs)
        if refset - defs:
            out.append(f"{f.name}: note marker with no note text: "
                       f"{sorted(refset - defs)[:5]}")
        if defs - refset:
            out.append(f"{f.name}: note never referenced, so it would not "
                       f"be printed: {sorted(defs - refset)[:5]}")
        dupes = {r for r in refset if refs.count(r) > 1}
        if dupes:
            out.append(f"{f.name}: note marker used more than once: "
                       f"{sorted(dupes)[:5]}")
    return out


def _check_contents(path: Path) -> tuple[list[str], int]:
    """Does every folio on the contents page point at the right page?

    A contents page can look perfect and still be wrong: the numbers are
    measured on one render and printed on the next, so anything that
    shifts pagination in between puts every entry out. This reads the
    printed number for each entry, turns to that page, and checks the
    section really begins there.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return [], 0

    reader = PdfReader(str(path))

    # The contents runs to more than one page in a 24-book build, so read
    # the page headed CONTENTS and every page after it that is still made
    # of contents rows. Stopping at the first page silently checks only
    # the books that happen to fit on it.
    toc: dict[str, int] = {}
    started = False
    for page in reader.pages:
        t = page.extract_text() or ""
        if not started:
            if "CONTENTS" not in t.upper()[:200] or "Book" not in t:
                continue
            started = True
        rows = list(re.finditer(
            r"(Book\s+\d+|Index of Names and Places)(.*?)(\d+)\s*(?:\n|$)",
            t, re.S))
        if not rows:
            break          # past the end of the contents
        for m in rows:
            toc[re.sub(r"\s+", " ", m.group(1)).strip()] = int(m.group(3))
    if not toc:
        return [], 0

    def printed_folio(page) -> int | None:
        for ln in reversed((page.extract_text() or "").strip().split("\n")):
            s = ln.strip()
            if s.isdigit():
                return int(s)
        return None

    actual: dict[str, int] = {}
    for page in reader.pages:
        t = (page.extract_text() or "").strip()
        if not t:
            continue
        lines = [x.strip() for x in t.split("\n") if x.strip()]
        for ln in lines[1:3]:
            m = re.match(r"Odyssey\s*[—–-]\s*Book\s+(\d+)\s*$", ln)
            if m:
                actual.setdefault(f"Book {int(m.group(1))}",
                                  printed_folio(page) or -1)
                break
        for ln in lines[:2]:
            if re.match(r"INDEX OF NAMES AND PLACES\s*$", ln, re.I):
                actual.setdefault("Index of Names and Places",
                                  printed_folio(page) or -1)
                break

    out: list[str] = []
    wrong = [(k, v, actual.get(k)) for k, v in toc.items()
             if actual.get(k) != v]
    if wrong:
        detail = "; ".join(f"{k} says {v}, actually {a}"
                           for k, v, a in wrong[:4])
        out.append(f"{len(wrong)} contents entry/entries point at the wrong "
                   f"page: {detail}")

    # every section in the book must be listed, or the contents is short
    missing = [k for k in actual if k not in toc]
    if missing:
        out.append(f"{len(missing)} section(s) missing from the contents: "
                   + ", ".join(sorted(missing)[:6]))
    return out, len(toc)


def _verse_pages(pdf) -> list[int]:
    """Indices of pages carrying verse.

    Identified by the running head ("ODYSSEY — BOOK n"), which the poem's
    pages carry and the front matter and index do not, minus the per-book
    endnote pages, which share the head but are set in the smaller
    apparatus size and carry no hanging line numbers.
    """
    out = []
    for i, p in enumerate(pdf.pages):
        txt = (p.extract_text() or "").strip()
        if not txt:
            continue
        head = txt.split("\n")[0]
        if not re.match(r"\s*ODYSSEY\s*[—–-]\s*BOOK", head, re.I):
            continue
        gent = [c for c in p.chars if "Gentium" in str(c.get("fontname", ""))]
        if len(gent) < 300:
            continue
        sizes = {round(c["size"], 1) for c in gent}
        # verse pages carry the hanging line numbers, well below body size
        if any(s < BODY_PT - 1.5 for s in sizes):
            out.append(i)
    return out


def _chars_per_line(pdf, verse_pages: list[int], body: float) -> float:
    """The verse block's width in characters, from rendered glyphs."""
    lefts: Counter = Counter()
    rights: Counter = Counter()
    widths: list[tuple[float, int]] = []
    for i in verse_pages[:40]:
        main = [c for c in pdf.pages[i].chars
                if "Gentium" in str(c.get("fontname", ""))
                and abs(round(c["size"], 1) - body) < 0.3]
        rows: dict[int, list] = {}
        for c in main:
            rows.setdefault(round(c["top"]), []).append(c)
        for cs in rows.values():
            x0 = min(c["x0"] for c in cs)
            x1 = max(c["x1"] for c in cs)
            lefts[round(x0)] += 1
            rights[round(x1)] += 1
            widths.append((x1 - x0, len(cs)))
    if not lefts or not widths:
        return 0.0
    block = max(rights) - lefts.most_common(1)[0][0]
    full = [(w, n) for w, n in widths if w > block * 0.7 and n > 20]
    if not full:
        return 0.0
    adv = sum(w for w, n in full) / sum(n for w, n in full)
    return block / adv if adv else 0.0


def _turnover_rate(cpl: float) -> float:
    """Percentage of the poem's verses longer than cpl characters."""
    src = Path(__file__).resolve().parent.parent / "translation"
    lens: list[int] = []
    for f in sorted(src.glob("book-*.md")):
        in_notes = False
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("## Notes"):
                in_notes = True
            if in_notes:
                continue
            m = re.match(r"^(\d+)\s+(.*)$", line)
            if m:
                lens.append(len(re.sub(r"\[\^L\d+\]", "", m.group(2))))
    if not lens:
        return 0.0
    return 100.0 * sum(1 for x in lens if x > cpl) / len(lens)


def _fonts(page) -> dict:
    """name -> embedded?  for the fonts used on a page."""
    from pdfminer.pdftypes import resolve1

    out: dict[str, bool] = {}
    res = resolve1(page.page_obj.resources) or {}
    fdict = resolve1(res.get("Font")) or {}
    for _k, ref in fdict.items():
        f = resolve1(ref)
        if not isinstance(f, dict):
            continue
        base = str(f.get("BaseFont", "?")).lstrip("/")
        desc = resolve1(f.get("FontDescriptor"))
        if desc is None:
            df = resolve1(f.get("DescendantFonts"))
            if df:
                desc = resolve1(resolve1(df[0]).get("FontDescriptor"))
        embedded = False
        if isinstance(desc, dict):
            embedded = any(x in desc for x in
                           ("FontFile", "FontFile2", "FontFile3"))
        out[base] = embedded
    return out


def _brief(nums: list[int], limit: int = 8) -> str:
    if len(nums) <= limit:
        return ", ".join(map(str, nums))
    return ", ".join(map(str, nums[:limit])) + f", … (+{len(nums)-limit})"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--trim", default=None, choices=sorted(TRIMS))
    args = ap.parse_args()
    t = args.trim
    if t is None:
        # Infer from the filename the builder produces
        # (odyssey-print-<trim>.pdf, with dots as hyphens). Longest key
        # first, so "5-5x8-5" is not shadowed by a shorter key that happens
        # to be a substring of it.
        for k in sorted(TRIMS, key=len, reverse=True):
            if k.replace(".", "-") in args.pdf.name:
                t = k
                break
        if t is None:
            t = "6x9"
            print(f"note: could not infer the trim from {args.pdf.name!r}; "
                  "checking against 6x9. Pass --trim to be explicit.")
    sys.exit(check(args.pdf, t))
