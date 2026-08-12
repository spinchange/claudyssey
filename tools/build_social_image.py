#!/usr/bin/env python3
"""Build docs/social.jpg — the 1200x630 Open Graph card image.

art/claudyssey-social.svg is drawn at exactly 1200x630 (the Open Graph /
Twitter summary_large_image aspect). Nothing here rasterizes SVG directly,
so the render goes through the proven cover pipeline: build_cover_pdf's
build() renders the SVG to a PDF via calibre (which is what already
handles the gradients, patterns, and feTurbulence grain correctly), and
PyMuPDF rasterizes that page to a JPEG at exactly 1200x630.

calibre quantizes the page size to a 1.2pt grid, so the page comes out a
fraction of a point taller than the artwork, with the art anchored at the
top-left and a hairline white band below it. That is why this script does
not reuse build_cover_pdf's whole-page verify: it clips the raster to the
artwork's true extent (page width x width*630/1200) and then checks the
finished JPEG's own edges for white instead.

The generated pages reference the result as {SITE}/social.jpg (see
social_meta() in build_web.py), so rebuild this after any change to the
social artwork:

    python tools/build_social_image.py
"""
from __future__ import annotations
from pathlib import Path

import build_cover_pdf

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "art" / "claudyssey-social.svg"
PDF = ROOT / "art" / "claudyssey-social.pdf"
OUT = ROOT / "docs" / "social.jpg"
W, H = 1200, 630


def check_edges(pix) -> list[str]:
    """No near-white pixels on any edge of the finished card."""
    px, w, h, n = pix.samples, pix.width, pix.height, pix.n

    def near_white(x: int, y: int) -> bool:
        o = (y * w + x) * n
        return min(px[o], px[o + 1], px[o + 2]) > 235

    problems = []
    for name, pts in [
        ("top", [(x, 0) for x in range(w)]),
        ("bottom", [(x, h - 1) for x in range(w)]),
        ("left", [(0, y) for y in range(h)]),
        ("right", [(w - 1, y) for y in range(h)]),
    ]:
        bad = sum(1 for x, y in pts if near_white(x, y))
        if bad:
            problems.append(f"{name} edge: {bad}/{len(pts)} near-white")
    return problems


def main() -> None:
    build_cover_pdf.build(SVG, 12.0, None, 0.0, PDF)

    import pymupdf
    doc = pymupdf.open(PDF)
    page = doc[0]
    art_w = page.rect.width
    art_h = art_w * H / W  # the artwork's extent; below it is the sliver
    clip = pymupdf.Rect(0, 0, art_w, art_h)
    mat = pymupdf.Matrix(W / art_w, H / art_h)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    if (pix.width, pix.height) != (W, H):
        raise SystemExit(f"rendered {pix.width}x{pix.height}, "
                         f"expected {W}x{H}")
    problems = check_edges(pix)
    if problems:
        raise SystemExit("card does not reach its edges:\n  "
                         + "\n  ".join(problems))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pix.save(OUT, jpg_quality=88)
    doc.close()
    print(f"wrote {OUT}  ({OUT.stat().st_size:,} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
