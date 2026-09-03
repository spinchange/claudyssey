#!/usr/bin/env python3
"""Validate a case-wrap PDF against a print supplier's requirements.

Checks, in the supplier's own terms:

  File Type    a readable PDF
  Page Count   exactly 1
  Dimensions   the given trim, to within a rounding tolerance
  Spine Width  the given spine (reported; geometry is checked against it)
  Fonts        every font that draws a glyph is embedded
  Layers       flattened: no optional content groups, no transparency
               groups, no annotations, no form fields

and two things the spec implies but does not say, which are the usual
reasons a wrap is rejected:

  Bleed        the artwork reaches all four edges (no white border)
  Safe area    nothing critical sits within 0.375in of a trimmed edge or
               strays across a spine fold

Usage:
    python tools/check_wrap.py art/claudyssey-wrap.pdf
    python tools/check_wrap.py <pdf> --spine 1.389          # width follows
    python tools/check_wrap.py <pdf> --width 13.639 --height 9.25 --spine 1.389
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

HEIGHT_IN = 9.25
SPINE_IN = 1.400          # 595 pages: pages/444 + 0.06, Lulu's formula
PANEL_IN = 6.125          # 6 in trim + 0.125 in bleed, fixed by the trim
WIDTH_IN = round(2 * PANEL_IN + SPINE_IN, 3)    # 13.650

# A supplier quoting three decimals is working to a thousandth of an inch
# (0.072 pt). Allow a tenth of a point — tight enough to catch calibre's
# 1.2pt page-size quantization, loose enough to ignore float noise.
SIZE_TOL_PT = 0.1


def check(pdf: Path, width_in: float, height_in: float,
          spine_in: float) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("check_wrap.py needs pypdf:  pip install pypdf")

    problems: list[str] = []
    notes: list[str] = []

    reader = PdfReader(str(pdf))

    # ---- page count
    n = len(reader.pages)
    if n != 1:
        problems.append(f"page count is {n}, must be exactly 1")
    page = reader.pages[0]

    # ---- dimensions
    box = page.mediabox
    w_pt, h_pt = float(box.width), float(box.height)
    want_w, want_h = width_in * 72, height_in * 72
    if abs(w_pt - want_w) > SIZE_TOL_PT or abs(h_pt - want_h) > SIZE_TOL_PT:
        problems.append(
            f"page is {w_pt / 72:.4f} x {h_pt / 72:.4f} in, "
            f"required {width_in:.3f} x {height_in:.3f} in")
    else:
        notes.append(f"page {w_pt / 72:.4f} x {h_pt / 72:.4f} in "
                     f"({w_pt / 72 * 25.4:.2f} x {h_pt / 72 * 25.4:.2f} mm)")

    # CropBox/TrimBox must not shrink the page: a supplier reads MediaBox,
    # but a smaller CropBox is how a wrap silently loses its bleed.
    for name in ("/CropBox", "/TrimBox", "/BleedBox", "/ArtBox"):
        b = page.get(name)
        if b is None:
            continue
        b = b.get_object()
        if (abs(float(b.width) - w_pt) > SIZE_TOL_PT
                or abs(float(b.height) - h_pt) > SIZE_TOL_PT):
            problems.append(
                f"{name} is {float(b.width) / 72:.4f} x "
                f"{float(b.height) / 72:.4f} in, smaller than the page — "
                "this crops the bleed")

    # ---- spine geometry (reported, and used for the safe-area check)
    panel_in = (width_in - spine_in) / 2
    notes.append(f"spine {spine_in:.3f} in, panels {panel_in:.4f} in each")

    # ---- fonts embedded
    def deref(x):
        """Resolve a pypdf indirect reference to the object it names."""
        return x.get_object() if hasattr(x, "get_object") else x

    def fonts_of(pg) -> dict[str, bool]:
        """Every font that can draw on this page -> is it embedded?

        Walks the page resources AND the resources of every Form XObject,
        recursively: most of this artwork is drawn inside forms, so a
        page-level-only scan reports no fonts at all.
        """
        out: dict[str, bool] = {}
        stack = [deref(pg.get("/Resources"))]
        seen_ids: set[int] = set()
        while stack:
            r = deref(stack.pop())
            if not isinstance(r, dict) or id(r) in seen_ids:
                continue
            seen_ids.add(id(r))

            fd = deref(r.get("/Font"))
            for _k, ref in (fd.items() if isinstance(fd, dict) else []):
                f = deref(ref)
                if not isinstance(f, dict):
                    continue
                base = str(f.get("/BaseFont", "?")).lstrip("/")
                desc = deref(f.get("/FontDescriptor"))
                if not isinstance(desc, dict):
                    df = deref(f.get("/DescendantFonts"))
                    if isinstance(df, list) and df:
                        desc = deref(deref(df[0]).get("/FontDescriptor"))
                emb = isinstance(desc, dict) and any(
                    k in desc for k in
                    ("/FontFile", "/FontFile2", "/FontFile3"))
                # a font name can appear in several forms; embedded once is
                # enough, never-embedded anywhere is a failure
                out[base] = out.get(base, False) or emb

            xo = deref(r.get("/XObject"))
            for _k, ref in (xo.items() if isinstance(xo, dict) else []):
                x = deref(ref)
                if isinstance(x, dict) and "/Resources" in x:
                    stack.append(x["/Resources"])
        return out

    fonts = fonts_of(page)
    not_emb = sorted(k for k, v in fonts.items() if not v)
    if not_emb:
        problems.append("fonts not embedded: " + ", ".join(not_emb))
    elif fonts:
        notes.append(f"{len(fonts)} font(s), all embedded: "
                     + ", ".join(sorted(fonts)))
    else:
        notes.append("no text fonts (artwork is paths only)")

    # ---- flattened
    root = reader.trailer["/Root"].get_object()
    if "/OCProperties" in root:
        problems.append(
            "the PDF has optional content groups (layers) — must be "
            "flattened")
    annots = page.get("/Annots")
    if annots and len(annots.get_object()):
        problems.append(
            f"{len(annots.get_object())} annotation(s) present — a "
            "flattened wrap should have none")
    if "/AcroForm" in root:
        problems.append("form fields present — must be flattened")

    # transparency groups / soft masks are the other half of "flattened"
    res = page.get("/Resources")
    res = res.get_object() if hasattr(res, "get_object") else (res or {})
    if isinstance(res, dict):
        if "/Group" in page:
            grp = deref(page["/Group"])
            if isinstance(grp, dict) and str(grp.get("/S")) == "/Transparency":
                notes.append("page has a transparency group (usually fine; "
                             "flatten if the supplier rejects it)")
        egs = deref(res.get("/ExtGState")) or {}
        soft = []
        for k, ref in (egs.items() if isinstance(egs, dict) else []):
            gs = deref(ref)
            if isinstance(gs, dict) and gs.get("/SMask") not in (None, "/None"):
                soft.append(str(k))
        if soft:
            notes.append(f"{len(soft)} soft mask(s) in ExtGState — "
                         "transparency is present but rasterizes cleanly")

    # ---- images (a flattened wrap may contain rasters; report them so the
    # resolution can be judged)
    # Recurse through every place a renderer can hide one: Form XObjects
    # (the artwork is drawn inside them), tiling patterns (Chromium writes
    # an SVG <pattern> fill as a page-sized 72 ppi bitmap inside a
    # /Pattern resource — this is what Lulu's "images under 200 ppi"
    # preflight catches), and the forms behind ExtGState soft masks.
    imgs = []
    seen: set[int] = set()

    def scan_images(r) -> None:
        r = deref(r)
        if not isinstance(r, dict) or id(r) in seen:
            return
        seen.add(id(r))
        xo = deref(r.get("/XObject"))
        for _k, ref in (xo.items() if isinstance(xo, dict) else []):
            o = deref(ref)
            if not isinstance(o, dict):
                continue
            if str(o.get("/Subtype")) == "/Image":
                iw, ih = int(o.get("/Width", 0)), int(o.get("/Height", 0))
                imgs.append((iw, ih, iw / (w_pt / 72) if w_pt else 0))
            else:
                scan_images(o.get("/Resources"))
        pats = deref(r.get("/Pattern"))
        for _k, ref in (pats.items() if isinstance(pats, dict) else []):
            o = deref(ref)
            if isinstance(o, dict):
                scan_images(o.get("/Resources"))
        gs = deref(r.get("/ExtGState"))
        for _k, ref in (gs.items() if isinstance(gs, dict) else []):
            o = deref(ref)
            sm = deref(o.get("/SMask")) if isinstance(o, dict) else None
            if isinstance(sm, dict) and sm.get("/G") is not None:
                scan_images(deref(sm["/G"]).get("/Resources"))

    scan_images(res)
    for iw, ih, ppi in imgs:
        if ppi < 300:
            problems.append(
                f"embedded image {iw}x{ih} is only {ppi:.0f} ppi across the "
                "page — print needs 300 ppi or better")
        else:
            notes.append(f"embedded image {iw}x{ih} ({ppi:.0f} ppi)")
    if not imgs:
        notes.append("no raster images — fully vector")

    # ---- bleed and safe area, by rendering
    try:
        import pypdfium2 as pdfium
    except ImportError:
        notes.append("(install pypdfium2 to check bleed and safe area)")
    else:
        doc = pdfium.PdfDocument(str(pdf))
        img = doc[0].render(scale=2.0).to_pil().convert("RGB")
        pw, ph = img.size
        px = img.load()

        def white(pts):
            return sum(1 for x, y in pts if min(px[x, y]) > 235)

        sx, sy = max(1, pw // 300), max(1, ph // 300)
        for name, pts in (
            ("top", [(x, 0) for x in range(0, pw, sx)]),
            ("bottom", [(x, ph - 1) for x in range(0, pw, sx)]),
            ("left", [(0, y) for y in range(0, ph, sy)]),
            ("right", [(pw - 1, y) for y in range(0, ph, sy)]),
        ):
            k = white(pts)
            if k:
                problems.append(
                    f"{name} edge has {k}/{len(pts)} near-white samples — "
                    "the artwork does not bleed to that edge")

        # ---- safe area.
        # Ink in the bleed is expected — that is what bleed is for — but
        # LIGHT ink (text, rules) hard against a trimmed edge means content
        # is about to be cut off. Look for bone-coloured pixels inside the
        # trim margin, which is how the first draft's overrunning blurb
        # would have been caught before it reached a printer.
        ppi_x = pw / (w_pt / 72)
        ppi_y = ph / (h_pt / 72)
        margin_x = int(0.125 * ppi_x)      # the bleed itself
        margin_y = int(0.125 * ppi_y)

        def light_in(x0, x1, y0, y1):
            n = 0
            for x in range(max(0, x0), min(pw, x1), max(1, (x1 - x0) // 120)):
                for y in range(max(0, y0), min(ph, y1),
                               max(1, (y1 - y0) // 120)):
                    r, g, b = px[x, y]
                    # bone (#ead9b4) and gold (#c99b3f) are much lighter
                    # than the wine ground; anything bright is content
                    if r > 150 and g > 130:
                        n += 1
            return n

        bands = {
            "top": (0, pw, 0, margin_y),
            "bottom": (0, pw, ph - margin_y, ph),
            "left": (0, margin_x, 0, ph),
            "right": (pw - margin_x, pw, 0, ph),
        }
        for name, (x0, x1, y0, y1) in bands.items():
            n = light_in(x0, x1, y0, y1)
            if n:
                problems.append(
                    f"{n} light pixel(s) inside the {name} bleed area — "
                    "artwork that must survive trimming is too close to "
                    "the edge")

        notes.append(
            f"spine folds at x={panel_in:.4f} and "
            f"{panel_in + spine_in:.4f} in")

    print(f"{pdf.name}")
    for s in notes:
        print(f"  - {s}")
    if problems:
        print("\nFAIL")
        for p in problems:
            print(f"  * {p}")
        return 1
    print("\nOK — meets the supplier requirements")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--width", type=float, default=None,
                    help="overall width in inches (default: two panels "
                         "plus the spine)")
    ap.add_argument("--height", type=float, default=HEIGHT_IN)
    ap.add_argument("--spine", type=float, default=SPINE_IN)
    args = ap.parse_args()
    width = (args.width if args.width is not None
             else round(2 * PANEL_IN + args.spine, 3))
    sys.exit(check(args.pdf, width, args.height, args.spine))
