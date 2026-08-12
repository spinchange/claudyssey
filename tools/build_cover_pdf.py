#!/usr/bin/env python3
"""Render an SVG in art/ to a full-bleed, borderless single-page PDF.

The page is sized to the SVG's own aspect ratio and the artwork is laid
edge to edge: no margins, no white border, one page.

Why it is done this way (established by measuring output, not from docs):

  * The SVG is placed with an <img> tag and NOT inlined. calibre's
    html->epub step rewrites inline SVG and drops <defs>, so the gradients,
    the meander/zigzag/dot patterns and the grain filter all disappear —
    the cover comes out as a bare bone-coloured field. Referenced as an
    image the file is passed through untouched.
  * --pdf-no-cover, or calibre inserts its own cover page and the output is
    two pages with the first one blank.
  * Every --margin-* and --pdf-page-margin-* is zeroed. The artwork already
    carries its own frame inset; any page margin on top of that shows as a
    white border, which is the one thing a full-bleed cover must not have.
  * Output is vector (paths + embedded Palatino text). The one raster in
    the file is the feTurbulence grain layer, which has no PDF primitive
    and so is rasterized by the renderer at ~300ppi. That is correct: the
    grain is part of the design.

Usage:
    python tools/build_cover_pdf.py                    # the book cover
    python tools/build_cover_pdf.py --svg art/x.svg    # any other art
    python tools/build_cover_pdf.py --width 6          # 6in wide page
    python tools/build_cover_pdf.py --bleed 0.125      # add print bleed
"""
from __future__ import annotations
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"
OUT_DIR = ART
WORK = ROOT / "print-build" / "cover-work"

EBOOK_CONVERT = (
    os.environ.get("EBOOK_CONVERT")
    or shutil.which("ebook-convert")
    or r"C:\Program Files\Calibre2\ebook-convert.exe"
)

# Page width in inches when none is given. 8x12 at the cover's 2:3 ratio is
# a convenient full-screen/presentation size and a common poster proportion.
DEFAULT_WIDTH_IN = 8.0


def svg_aspect(path: Path) -> tuple[float, float]:
    """(width, height) in the SVG's own user units.

    Prefers the viewBox, which is what actually governs the drawing, and
    falls back to the width/height attributes.
    """
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    m = re.search(r'viewBox\s*=\s*["\']\s*([-\d.]+)[,\s]+([-\d.]+)'
                  r'[,\s]+([\d.]+)[,\s]+([\d.]+)', head)
    if m:
        return float(m.group(3)), float(m.group(4))
    w = re.search(r'\swidth\s*=\s*["\']([\d.]+)', head)
    h = re.search(r'\sheight\s*=\s*["\']([\d.]+)', head)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    sys.exit(f"cannot determine the size of {path.name}: "
             "no viewBox and no width/height")


def build(svg: Path, width_in: float | None, height_in: float | None,
          bleed_in: float, out: Path | None) -> Path:
    if not svg.exists():
        sys.exit(f"missing {svg}")

    uw, uh = svg_aspect(svg)
    ratio = uh / uw

    # Page size: honour whichever dimension was given and derive the other
    # from the artwork's aspect, so the image is never distorted.
    if width_in and height_in:
        pw, ph = width_in, height_in
    elif height_in:
        ph = height_in
        pw = ph / ratio
    else:
        pw = width_in or DEFAULT_WIDTH_IN
        ph = pw * ratio

    # Bleed grows the page on all four sides; the artwork is scaled to the
    # bled size so the design still runs off every trimmed edge.
    pw += 2 * bleed_in
    ph += 2 * bleed_in

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copy(svg, WORK / svg.name)

    # width/height 100% on both the html and the img, with every default
    # margin zeroed, so the artwork fills the page corner to corner.
    (WORK / "cover.html").write_text(
        "<!DOCTYPE html>\n"
        '<html><head><meta charset="utf-8"/><title>Cover</title>\n'
        "<style>\n"
        f"  @page {{ size: {pw:.4f}in {ph:.4f}in; margin: 0; }}\n"
        "  html, body { margin:0; padding:0; border:0; width:100%;"
        " height:100%; overflow:hidden; }\n"
        "  img { display:block; margin:0; padding:0; border:0;"
        " width:100%; height:100%; }\n"
        "</style></head><body>\n"
        f'<img src="{svg.name}" alt=""/>\n'
        "</body></html>\n",
        encoding="utf-8")

    if out is None:
        out = OUT_DIR / (svg.stem + ".pdf")

    cmd = [
        EBOOK_CONVERT, str(WORK / "cover.html"), str(out),
        "--custom-size", f"{pw:.4f}x{ph:.4f}",
        "--unit", "inch",
        # Both margin families must be zero: the content margins position
        # the artwork, the pdf page margins add an outer box around it.
        "--margin-left", "0", "--margin-right", "0",
        "--margin-top", "0", "--margin-bottom", "0",
        "--pdf-page-margin-left", "0", "--pdf-page-margin-right", "0",
        "--pdf-page-margin-top", "0", "--pdf-page-margin-bottom", "0",
        # no running head, no folio, and no calibre-inserted cover page
        "--pdf-no-cover",
        "--disable-font-rescaling",
        "--embed-all-fonts",
        "--subset-embedded-fonts",
    ]
    print(f"rendering {svg.name} -> {pw:.3f}x{ph:.3f}in"
          + (f" (incl. {bleed_in}in bleed)" if bleed_in else ""))
    subprocess.run(cmd, check=True, cwd=WORK, stdout=subprocess.DEVNULL)

    shutil.rmtree(WORK, ignore_errors=True)
    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
    return out


def verify(pdf: Path) -> int:
    """Check the result is one page, right size, and edge to edge.

    A borderless cover fails in a way that is invisible in the numbers —
    a white band at one edge — so the check renders the page and samples
    its outermost pixels.
    """
    try:
        import pypdfium2 as pdfium
        from pypdf import PdfReader
    except ImportError:
        print("(install pypdf and pypdfium2 to verify the output)")
        return 0

    problems: list[str] = []
    r = PdfReader(str(pdf))
    if len(r.pages) != 1:
        problems.append(f"{len(r.pages)} pages, expected exactly 1")
    box = r.pages[0].mediabox
    pw, ph = float(box.width) / 72, float(box.height) / 72

    doc = pdfium.PdfDocument(str(pdf))
    img = doc[0].render(scale=2.0).to_pil().convert("RGB")
    w, h = img.size
    px = img.load()

    def near_white(samples):
        return sum(1 for x, y in samples if min(px[x, y]) > 235)

    step_x = max(1, w // 200)
    step_y = max(1, h // 200)
    edges = {
        "top": [(x, 0) for x in range(0, w, step_x)],
        "bottom": [(x, h - 1) for x in range(0, w, step_x)],
        "left": [(0, y) for y in range(0, h, step_y)],
        "right": [(w - 1, y) for y in range(0, h, step_y)],
    }
    for name, pts in edges.items():
        n = near_white(pts)
        if n:
            problems.append(
                f"{name} edge has {n}/{len(pts)} near-white samples — "
                "the artwork does not reach that edge")

    print(f"\n{pdf.name}: {len(r.pages)} page, {pw:.3f}x{ph:.3f}in")
    if problems:
        print("FAIL")
        for p in problems:
            print(f"  * {p}")
        return 1
    print("  full-bleed on all four edges, single page")
    print("OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", type=Path,
                    default=ART / "claudyssey-cover.svg",
                    help="source SVG (default: art/claudyssey-cover.svg)")
    ap.add_argument("--width", type=float, default=None,
                    help=f"page width in inches (default {DEFAULT_WIDTH_IN})")
    ap.add_argument("--height", type=float, default=None,
                    help="page height in inches (derived from the artwork "
                         "if omitted)")
    ap.add_argument("--bleed", type=float, default=0.0,
                    help="bleed in inches added to every side (e.g. 0.125)")
    ap.add_argument("-o", "--out", type=Path, default=None,
                    help="output path (default: alongside the SVG)")
    args = ap.parse_args()

    pdf = build(args.svg, args.width, args.height, args.bleed, args.out)
    sys.exit(verify(pdf))
