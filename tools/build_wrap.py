#!/usr/bin/env python3
"""Build the paperback case wrap — back cover, spine, and front cover as a
single flat landscape PDF, to a print-on-demand supplier's spec.

Default geometry is Lulu's spec for the 595-page 6x9 interior:

    trim            13.650 x 9.25 in   (346.71 x 234.95 mm)
    spine            1.400 in          (35.56 mm)
    panels           6.125 in each     = 6 in trim + 0.125 in bleed

The panels are fixed by the trim; only the spine moves with the page
count, and the overall width follows it (2 x 6.125 + spine). The spine
is Lulu's published paperback formula, the same for every paper stock
they offer (all are bulked at 444 pages per inch):

    spine (in) = pages / 444 + 0.06

(Lulu Book Creation Guide p.13; help.api.lulu.com, "How is spine width
calculated?"). It reproduces the spec Lulu issued for the earlier
590-page interior exactly — 590 / 444 + 0.06 = 1.3888 -> 1.389 in,
13.639 in wide — which is the check that pins the formula. A different
page count needs only --pages; --spine takes Lulu's own figure should the
upload step's Requirements panel ever disagree.

    +---------------------------+-------+---------------------------+
    |        back cover         | spine |       front cover         |
    |         6.125 in          | 1.400 |        6.125 in           |
    +---------------------------+-------+---------------------------+
    0                        6.125   7.525                     13.650

The artwork is generated rather than hand-placed: the front panel reuses
the existing cover design, the spine and back are built to match it.

Print requirements this targets, all verified by tools/check_wrap.py:
  * exactly 1 page at the given size
  * all fonts embedded and subsetted
  * flattened — no optional content groups (layers), no transparency
    groups, no annotations
  * full bleed to all four edges

Usage:
    python tools/build_wrap.py                   # the 595-page interior
    python tools/build_wrap.py --pages 604       # spine from the page count
    python tools/build_wrap.py --spine 1.42      # Lulu's figure, if it differs
    python tools/build_wrap.py --no-url          # omit the site URL
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"
WORK = ROOT / "print-build" / "wrap-work"

EBOOK_CONVERT = (
    os.environ.get("EBOOK_CONVERT")
    or shutil.which("ebook-convert")
    or r"C:\Program Files\Calibre2\ebook-convert.exe"
)

# ---- spec ---------------------------------------------------------------
WRAP_H_IN = 9.25
BLEED_IN = 0.125          # included in the panel and height figures above
PANEL_IN = 6.125          # 6 in trim + bleed on the outside edge
PAGES = 595               # print-build/odyssey-print-6x9.pdf, as built
PAGES_PER_INCH = 444      # Lulu's bulk for every paperback stock
SPINE_ADD_IN = 0.06       # Lulu's fixed allowance on top of the page block


def spine_for(pages: int) -> float:
    """Lulu's paperback spine width for a page count, to their precision."""
    return round(pages / PAGES_PER_INCH + SPINE_ADD_IN, 3)


def wrap_width(spine_in: float) -> float:
    """Overall width: two fixed panels and the spine between them."""
    return round(2 * PANEL_IN + spine_in, 3)


SPINE_IN = spine_for(PAGES)          # 1.400
WRAP_W_IN = wrap_width(SPINE_IN)     # 13.650

# The SVG is drawn in user units at 100 units per inch, which keeps every
# coordinate a readable number and is resolution-independent regardless.
UPI = 100.0

# Palette, from the existing cover (art/claudyssey-cover.svg).
WINE_TOP = "#46192b"
WINE_MID = "#331323"
WINE_BOT = "#1e0b15"
BONE = "#ead9b4"
GOLD = "#c99b3f"

SERIF = ("'Palatino Linotype','Book Antiqua',Palatino,Georgia,serif")

SITE_URL = "theclaudyssey.com"

BLURB = (
    "A complete line-for-line English translation of Homer\u2019s "
    "<tspan font-style=\"italic\">Odyssey</tspan> \u2014 all 24 books, "
    "12,107 lines, with one English line for every line of the Greek and "
    "the same line numbering throughout, so any passage can be cited as "
    "book.line and found in either language."
)

BLURB2 = (
    "The edition carries a scholarly apparatus of 1,260 line notes and an "
    "index of every named person, god, people, and place in the poem."
)

BLURB3 = (
    "Translated by Claude (Fable 5), a large language model, under the "
    "editorial direction of Chris Duffy. The translation is dedicated to "
    "the public domain under CC0 1.0: no permission or attribution is "
    "required for any use."
)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def strip_markup(s: str) -> str:
    """The visible text of a fragment, with any tags removed."""
    out, depth = [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


# Mean glyph advance as a fraction of the font size, for this Palatino text
# at these sizes. Measured from the rendered PDF rather than guessed: a
# too-generous figure is what pushed the first draft's blurb past the frame.
ADVANCE_RATIO = 0.50


def wrap_text(text: str, width_units: float, size: float) -> list[str]:
    """Greedy wrap to a pixel width, not a character count.

    Wrapping by characters cannot see that "1,260" or "book.line" are wide,
    so the line count is right but the lines overrun. This measures against
    the actual column width and leaves markup intact.
    """
    limit = width_units / (size * ADVANCE_RATIO)
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        probe = (cur + " " + w).strip()
        if len(strip_markup(probe)) > limit and cur:
            lines.append(cur)
            cur = w
        else:
            cur = probe
    if cur:
        lines.append(cur)
    return lines


def build_svg(spine_in: float, with_url: bool) -> str:
    panel_in = PANEL_IN
    W = wrap_width(spine_in) * UPI
    H = WRAP_H_IN * UPI
    P = panel_in * UPI
    S = spine_in * UPI
    B = BLEED_IN * UPI

    back_x = 0.0
    spine_x = P
    front_x = P + S

    # The safe area of each panel: inside the bleed on the outer edges and
    # in from the spine fold. Nothing that must survive trimming goes
    # outside this.
    safe = 0.375 * UPI          # 3/8in from every trimmed edge

    o: list[str] = []
    add = o.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W:.2f} {H:.2f}" '
        f'width="{W:.2f}" height="{H:.2f}" role="img" '
        f'aria-label="Paperback case wrap for Homer\u2019s Odyssey \u2014 '
        f'A Claudyssey: back cover, spine, and front cover.">')

    # ---- defs
    add('<defs>')
    add(f'<linearGradient id="wine" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{WINE_TOP}"/>'
        f'<stop offset="0.55" stop-color="{WINE_MID}"/>'
        f'<stop offset="1" stop-color="{WINE_BOT}"/></linearGradient>')
    add('<radialGradient id="vigF" cx="0.5" cy="0.42" r="0.85">'
        '<stop offset="0.6" stop-color="#000000" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#0c0408" stop-opacity="0.5"/>'
        '</radialGradient>')
    # meander band, drawn at the cover's proportions (40u tile at 800-wide;
    # here 1in = 100u, so the tile is scaled to sit in a 0.33in band)
    add(f'<pattern id="meander" width="50" height="50" '
        f'patternUnits="userSpaceOnUse">'
        f'<g fill="none" stroke="{BONE}" stroke-width="4.5">'
        f'<path d="M0 6.25 H50"/><path d="M0 42.5 H50"/>'
        f'<path d="M35 42.5 V13.75 H13.75 V32.5 H23.75"/></g></pattern>')
    add(f'<pattern id="dots" width="18.75" height="15" '
        f'patternUnits="userSpaceOnUse">'
        f'<circle cx="7.5" cy="7.5" r="3.25" fill="{BONE}"/></pattern>')
    add(f'<pattern id="zigzag" width="35" height="33.75" '
        f'patternUnits="userSpaceOnUse">'
        f'<g fill="none" stroke="{BONE}" stroke-width="3.75" '
        f'stroke-linejoin="miter">'
        f'<path d="M0 12.5 L17.5 2.5 L35 12.5"/>'
        f'<path d="M0 28.75 L17.5 18.75 L35 28.75"/></g></pattern>')
    add('</defs>')

    # ---- ground across the whole wrap, so the fold has no seam
    add(f'<rect x="0" y="0" width="{W:.2f}" height="{H:.2f}" '
        f'fill="url(#wine)"/>')
    # vignette over the front panel only, matching the original cover
    add(f'<rect x="{front_x:.2f}" y="0" width="{P:.2f}" height="{H:.2f}" '
        f'fill="url(#vigF)"/>')

    # =====================================================================
    # FRONT COVER  — the existing cover design, redrawn to this panel.
    # The original art is 800x1200 user units for a 6x9 trim; this panel is
    # 6.125x9.25in including bleed. Scale by the trim and centre, so the
    # design bleeds evenly on all three outer edges.
    # =====================================================================
    fs = (6.0 * UPI) / 800.0                 # original units -> panel units
    fx = front_x + B                          # trim origin inside the bleed
    fy = B
    add(f'<g transform="translate({fx:.3f},{fy:.3f}) scale({fs:.6f})">')
    add(front_panel_svg())
    add('</g>')

    # =====================================================================
    # SPINE
    # =====================================================================
    cx = spine_x + S / 2
    add(f'<g>')
    # hairline rules just inside each fold
    add(f'<line x1="{spine_x + 9:.2f}" y1="{safe:.2f}" '
        f'x2="{spine_x + 9:.2f}" y2="{H - safe:.2f}" '
        f'stroke="{BONE}" stroke-width="1" opacity="0.30"/>')
    add(f'<line x1="{spine_x + S - 9:.2f}" y1="{safe:.2f}" '
        f'x2="{spine_x + S - 9:.2f}" y2="{H - safe:.2f}" '
        f'stroke="{BONE}" stroke-width="1" opacity="0.30"/>')
    # Title reading top-to-bottom, the convention on English-language books.
    add(f'<g transform="translate({cx:.2f},{H / 2:.2f}) rotate(90)" '
        f'text-anchor="middle" font-family="{SERIF}">')
    add(f'<text x="0" y="-13" font-size="46" fill="{BONE}" '
        f'letter-spacing="2">HOMER\u2019S ODYSSEY</text>')
    add(f'<text x="0" y="26" font-size="24" fill="{GOLD}" '
        f'letter-spacing="3" opacity="0.95">A CLAUDYSSEY</text>')
    add('</g>')
    # small meander cap at each end of the spine
    for yy in (safe + 8, H - safe - 8 - 33):
        add(f'<rect x="{spine_x + 13:.2f}" y="{yy:.2f}" '
            f'width="{S - 26:.2f}" height="33" fill="url(#meander)" '
            f'opacity="0.85"/>')
    add('</g>')

    # =====================================================================
    # BACK COVER
    # =====================================================================
    # The frame mirrors the front cover's, inset from the trim. Everything
    # on the back is laid out INSIDE the frame with its own padding, so no
    # element can collide with the border or spill over a trimmed edge.
    fr_x = back_x + B + 24
    fr_y = B + 24
    fr_w = P - 2 * B - 48
    fr_h = H - 2 * B - 48
    pad = 46                       # breathing room inside the frame
    bx0 = fr_x + pad
    bx1 = fr_x + fr_w - pad
    bw = bx1 - bx0
    add('<g>')
    add(f'<rect x="{fr_x:.2f}" y="{fr_y:.2f}" width="{fr_w:.2f}" '
        f'height="{fr_h:.2f}" fill="none" stroke="{BONE}" '
        f'stroke-width="2.5" opacity="0.55"/>')

    # --- lay the fixed furniture out first, then fit the blurb in what is
    # left. The bands and the imprint have known heights; the blurb is the
    # only elastic part, so it is the one that must be measured to fit.
    band_h = 40
    top_band_y = fr_y + 30

    imprint_h = 70 if with_url else 34
    imprint_y = fr_y + fr_h - 30 - imprint_h

    wave_h = 44
    wave_y = imprint_y - 34 - wave_h
    rule_y = wave_y - 30

    epi_y = top_band_y + band_h + 62
    rule2_y = epi_y + 30

    text_top = rule2_y + 46
    text_bottom = rule_y - 30
    avail = text_bottom - text_top

    add(f'<rect x="{bx0:.2f}" y="{top_band_y:.2f}" width="{bw:.2f}" '
        f'height="{band_h}" fill="url(#meander)" opacity="0.9"/>')

    add(f'<g font-family="{SERIF}" fill="{BONE}">')
    add(f'<text x="{bx0 + bw / 2:.2f}" y="{epi_y:.2f}" font-size="26" '
        f'font-style="italic" text-anchor="middle" opacity="0.72">'
        f'\u1f04\u03bd\u03b4\u03c1\u03b1 \u03bc\u03bf\u03b9 '
        f'\u1f14\u03bd\u03bd\u03b5\u03c0\u03b5, '
        f'\u03bc\u03bf\u1fe6\u03c3\u03b1, '
        f'\u03c0\u03bf\u03bb\u03cd\u03c4\u03c1\u03bf\u03c0\u03bf\u03bd'
        f'</text>')
    add(f'<line x1="{bx0 + bw / 2 - 90:.2f}" y1="{rule2_y:.2f}" '
        f'x2="{bx0 + bw / 2 + 90:.2f}" y2="{rule2_y:.2f}" '
        f'stroke="{GOLD}" stroke-width="1.2" opacity="0.85"/>')

    # Fit the three paragraphs into `avail`, stepping the type down until
    # they do. Starting sizes are the design intent; the loop only shrinks.
    for scale in (1.0, 0.94, 0.88, 0.82, 0.76, 0.70):
        sizes = [22 * scale, 20 * scale, 19 * scale]
        leads = [s * 1.34 for s in sizes]
        gaps = [s * 0.75 for s in sizes]
        blocks = [wrap_text(t, bw, s) for t, s in
                  zip((BLURB, BLURB2, BLURB3), sizes)]
        total = sum(len(b) * l for b, l in zip(blocks, leads)) \
            + sum(gaps[:-1])
        if total <= avail:
            break

    y = text_top
    for lines, size, lead, gap, op in zip(
            blocks, sizes, leads, gaps, (0.92, 0.80, 0.72)):
        for line in lines:
            add(f'<text x="{bx0:.2f}" y="{y:.2f}" '
                f'font-size="{size:.2f}" opacity="{op}">{line}</text>')
            y += lead
        y += gap
    add('</g>')

    # wave band + rules, echoing the ship register on the front
    add(f'<line x1="{bx0:.2f}" y1="{rule_y:.2f}" x2="{bx1:.2f}" '
        f'y2="{rule_y:.2f}" stroke="{BONE}" stroke-width="2" '
        f'opacity="0.75"/>')
    add(f'<rect x="{bx0 + 10:.2f}" y="{rule_y + 8:.2f}" '
        f'width="{bw - 20:.2f}" height="13" fill="url(#dots)" '
        f'opacity="0.75"/>')
    add(f'<rect x="{bx0:.2f}" y="{wave_y:.2f}" width="{bw:.2f}" '
        f'height="{wave_h}" fill="url(#zigzag)" opacity="0.75"/>')

    # imprint block
    add(f'<g font-family="{SERIF}" fill="{BONE}" text-anchor="middle">')
    add(f'<text x="{bx0 + bw / 2:.2f}" y="{imprint_y + 20:.2f}" '
        f'font-size="18" opacity="0.62" letter-spacing="3">'
        f'TRANSLATION CC0 \u00b7 APPARATUS CC BY 4.0</text>')
    if with_url:
        add(f'<text x="{bx0 + bw / 2:.2f}" y="{imprint_y + 60:.2f}" '
            f'font-size="26" fill="{GOLD}" letter-spacing="2">'
            f'{esc(SITE_URL)}</text>')
    add('</g>')
    add('</g>')

    add('</svg>')
    return "\n".join(o)


def front_panel_svg() -> str:
    """The front cover artwork, in the original 800x1200 coordinate space.

    Kept as a faithful copy of art/claudyssey-cover.svg minus its own
    background rects and grain filter: the wrap paints one continuous
    ground across all three panels, and the feTurbulence grain is dropped
    because it is the one element that cannot be expressed as vector and
    would force a raster layer into the flattened output.
    """
    g = f'''
  <rect x="36" y="36" width="728" height="1128" fill="none"
        stroke="{BONE}" stroke-width="2.5" opacity="0.9"/>
  <rect x="48" y="48" width="704" height="1104" fill="none"
        stroke="{BONE}" stroke-width="1" opacity="0.4"/>
  <rect x="80" y="72" width="640" height="40" fill="url(#meanderF)"/>
  <g font-family="{SERIF}" text-anchor="middle">
    <text x="400" y="208" font-size="27" font-style="italic"
          fill="{BONE}" opacity="0.8">&#7940;&#957;&#948;&#961;&#945; &#956;&#959;&#953; &#7956;&#957;&#957;&#949;&#960;&#949;, &#956;&#959;&#8166;&#963;&#945;, &#960;&#959;&#955;&#973;&#964;&#961;&#959;&#960;&#959;&#957;</text>
    <text x="400" y="246" font-size="19" fill="{BONE}"
          opacity="0.55">Tell me the man, Muse &#8212; the man of many turnings</text>
  </g>
  <g font-family="{SERIF}" text-anchor="middle" fill="{BONE}">
    <text x="400" y="356" font-size="44" textLength="320"
          lengthAdjust="spacingAndGlyphs">HOMER&#8217;S</text>
    <text x="400" y="454" font-size="86" textLength="632"
          lengthAdjust="spacingAndGlyphs">ODYSSEY</text>
    <line x1="280" y1="486" x2="520" y2="486" stroke="{GOLD}"
          stroke-width="1.3" opacity="0.9"/>
    <text x="400" y="526" font-size="30" fill="{GOLD}" textLength="280"
          lengthAdjust="spacingAndGlyphs">&#927;&#916;&#933;&#931;&#931;&#917;&#921;&#913;</text>
    <text x="400" y="568" font-size="18" letter-spacing="2"><tspan fill-opacity="0.78">LINE FOR LINE TRANSLATION BY FABLE 5</tspan><tspan fill="{GOLD}" dx="7">&#183; A CLAUDYSSEY</tspan></text>
  </g>
  <line x1="90" y1="600" x2="710" y2="600" stroke="{BONE}" stroke-width="2"/>
  <rect x="100" y="606" width="600" height="12" fill="url(#dotsF)"/>
  <line x1="90" y1="626" x2="710" y2="626" stroke="{BONE}" stroke-width="2"/>
  <g stroke-linecap="round">
    <path d="M400 640 L262 790 M400 640 L538 790" stroke="{BONE}"
          stroke-width="2" opacity="0.75" fill="none"/>
    <line x1="400" y1="798" x2="400" y2="638" stroke="{BONE}" stroke-width="7"/>
    <line x1="336" y1="656" x2="464" y2="656" stroke="{BONE}" stroke-width="5"/>
    <g stroke="{BONE}" stroke-width="2.5" opacity="0.85">
      <g transform="translate(196,672)">
        <line x1="-12" y1="0" x2="12" y2="0"/><line x1="0" y1="-12" x2="0" y2="12"/>
        <line x1="-8.5" y1="-8.5" x2="8.5" y2="8.5"/><line x1="-8.5" y1="8.5" x2="8.5" y2="-8.5"/>
        <circle cx="0" cy="0" r="3.5" fill="{BONE}" stroke="none"/>
      </g>
      <g transform="translate(604,672)">
        <line x1="-12" y1="0" x2="12" y2="0"/><line x1="0" y1="-12" x2="0" y2="12"/>
        <line x1="-8.5" y1="-8.5" x2="8.5" y2="8.5"/><line x1="-8.5" y1="8.5" x2="8.5" y2="-8.5"/>
        <circle cx="0" cy="0" r="3.5" fill="{BONE}" stroke="none"/>
      </g>
    </g>
    <path d="M152 688 C158 776 240 828 400 828 C555 828 638 778 654 680 C640 754 540 802 400 802 C262 802 170 764 160 692 Z"
          fill="{BONE}" stroke="{BONE}" stroke-width="3" stroke-linejoin="round"/>
    <path d="M162 692 C150 664 141 634 138 606" fill="none" stroke="{BONE}" stroke-width="9"/>
    <circle cx="136" cy="598" r="7" fill="none" stroke="{BONE}" stroke-width="4"/>
    <path d="M648 686 C658 660 660 632 656 610" fill="none" stroke="{BONE}" stroke-width="9"/>
    <circle cx="654" cy="603" r="6.5" fill="{BONE}"/>
    <path d="M659 601 L678 595 L661 611 Z" fill="{BONE}"/>
    <line x1="176" y1="776" x2="146" y2="862" stroke="{BONE}" stroke-width="5"/>
    <g fill="{BONE}" stroke="{BONE}">
      <g transform="translate(258,786)">
        <path d="M-11 0 L11 0 L0 -28 Z" stroke="none"/><circle cx="0" cy="-40" r="8.5" stroke="none"/>
        <path d="M0 -20 L16 -6" fill="none" stroke-width="4"/><line x1="14" y1="-10" x2="44" y2="58" stroke-width="4"/>
      </g>
      <g transform="translate(328,796)">
        <path d="M-11 0 L11 0 L0 -28 Z" stroke="none"/><circle cx="0" cy="-40" r="8.5" stroke="none"/>
        <path d="M0 -20 L16 -6" fill="none" stroke-width="4"/><line x1="14" y1="-10" x2="44" y2="58" stroke-width="4"/>
      </g>
      <g transform="translate(472,796)">
        <path d="M-11 0 L11 0 L0 -28 Z" stroke="none"/><circle cx="0" cy="-40" r="8.5" stroke="none"/>
        <path d="M0 -20 L16 -6" fill="none" stroke-width="4"/><line x1="14" y1="-10" x2="44" y2="58" stroke-width="4"/>
      </g>
      <g transform="translate(542,786)">
        <path d="M-11 0 L11 0 L0 -28 Z" stroke="none"/><circle cx="0" cy="-40" r="8.5" stroke="none"/>
        <path d="M0 -20 L16 -6" fill="none" stroke-width="4"/><line x1="14" y1="-10" x2="44" y2="58" stroke-width="4"/>
      </g>
    </g>
  </g>
  <rect x="106" y="832" width="588" height="54" fill="url(#zigzagF)"/>
  <line x1="90" y1="896" x2="710" y2="896" stroke="{BONE}" stroke-width="2"/>
  <rect x="100" y="902" width="600" height="12" fill="url(#dotsF)"/>
  <line x1="90" y1="922" x2="710" y2="922" stroke="{BONE}" stroke-width="2"/>
  <g font-family="{SERIF}" text-anchor="middle" fill="{BONE}">
    <text x="400" y="978" font-size="18" opacity="0.7"
          letter-spacing="6">TRANSLATED BY</text>
    <text x="400" y="1026" font-size="44" textLength="260"
          lengthAdjust="spacingAndGlyphs">CLAUDE</text>
    <text x="400" y="1062" font-size="18" font-style="italic"
          opacity="0.6">24 books &#183; 12,107 lines rendered from the Greek</text>
  </g>
  <rect x="80" y="1088" width="640" height="40" fill="url(#meanderF)"/>
'''
    return g


def front_defs() -> str:
    """Patterns for the front panel, at its own 800x1200 scale."""
    return (
        f'<pattern id="meanderF" width="40" height="40" '
        f'patternUnits="userSpaceOnUse">'
        f'<g fill="none" stroke="{BONE}" stroke-width="3.6">'
        f'<path d="M0 5 H40"/><path d="M0 34 H40"/>'
        f'<path d="M28 34 V11 H11 V26 H19"/></g></pattern>'
        f'<pattern id="zigzagF" width="28" height="27" '
        f'patternUnits="userSpaceOnUse">'
        f'<g fill="none" stroke="{BONE}" stroke-width="3" '
        f'stroke-linejoin="miter">'
        f'<path d="M0 10 L14 2 L28 10"/>'
        f'<path d="M0 23 L14 15 L28 23"/></g></pattern>'
        f'<pattern id="dotsF" width="15" height="12" '
        f'patternUnits="userSpaceOnUse">'
        f'<circle cx="6" cy="6" r="2.6" fill="{BONE}"/></pattern>'
    )


def build(spine_in: float, with_url: bool, out: Path) -> Path:
    svg = build_svg(spine_in, with_url)
    # splice the front panel's own pattern defs into the shared <defs>
    svg = svg.replace('</defs>', front_defs() + '</defs>', 1)

    svg_path = ART / "claudyssey-wrap.svg"
    svg_path.write_text(svg, encoding="utf-8")
    print(f"wrote {svg_path}  ({len(svg):,} bytes)")

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copy(svg_path, WORK / svg_path.name)

    w, h = wrap_width(spine_in), WRAP_H_IN
    (WORK / "wrap.html").write_text(
        "<!DOCTYPE html>\n"
        '<html><head><meta charset="utf-8"/><title>Wrap</title>\n'
        "<style>\n"
        f"  @page {{ size: {w:.4f}in {h:.4f}in; margin: 0; }}\n"
        "  html, body { margin:0; padding:0; border:0; width:100%;"
        " height:100%; overflow:hidden; }\n"
        "  img { display:block; margin:0; padding:0; border:0;"
        " width:100%; height:100%; }\n"
        "</style></head><body>\n"
        f'<img src="{svg_path.name}" alt=""/>\n'
        "</body></html>\n",
        encoding="utf-8")

    cmd = [
        EBOOK_CONVERT, str(WORK / "wrap.html"), str(out),
        "--custom-size", f"{w:.4f}x{h:.4f}",
        "--unit", "inch",
        "--margin-left", "0", "--margin-right", "0",
        "--margin-top", "0", "--margin-bottom", "0",
        "--pdf-page-margin-left", "0", "--pdf-page-margin-right", "0",
        "--pdf-page-margin-top", "0", "--pdf-page-margin-bottom", "0",
        "--pdf-no-cover",
        "--disable-font-rescaling",
        "--embed-all-fonts",
        "--subset-embedded-fonts",
    ]
    print(f"rendering wrap -> {w:.3f}x{h:.3f}in "
          f"(spine {spine_in:.3f}in, panels "
          f"{(w - spine_in) / 2:.3f}in)")
    subprocess.run(cmd, check=True, cwd=WORK, stdout=subprocess.DEVNULL)
    shutil.rmtree(WORK, ignore_errors=True)

    _set_exact_page_size(out, w, h)

    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
    return out


def _set_exact_page_size(pdf: Path, w_in: float, h_in: float) -> None:
    """Force the page boxes to the exact required size.

    calibre quantizes --custom-size to a 1.2 pt grid: asking for 13.639in
    (982.008 pt) yields a 982.080 pt page, and the next step down is
    980.880 — it cannot express the value. (13.650 in is 982.8 pt, on the
    grid by luck; the next page count will not be.) A supplier quoting
    three decimals may reject a page that is a thousandth of an inch out,
    so the boxes are set exactly here.

    The artwork itself is already the right size: it is laid out to the
    CSS page (the exact figure), anchored at the top-left corner, and only
    the PDF page around it is the quantized size. So the boxes are cut to
    the wanted size from the top-left and the drawing is left alone.
    (Scaling the drawing to the quantized page, as an earlier version did,
    shrank it below the page and left a hairline of white down the right
    edge — 0.46 pt at this width, enough for the bleed check to catch.)
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, FloatObject, NameObject

    want_w, want_h = w_in * 72.0, h_in * 72.0
    reader = PdfReader(str(pdf))
    writer = PdfWriter()
    page = reader.pages[0]
    got_h = float(page.mediabox.height)

    # PDF y runs upward from the bottom, so top-left anchoring means the
    # box keeps the top edge and drops any excess height at the bottom.
    x0, y0 = 0.0, got_h - want_h
    for name in ("/MediaBox", "/CropBox", "/TrimBox", "/BleedBox",
                 "/ArtBox"):
        if name == "/MediaBox" or name in page:
            page[NameObject(name)] = ArrayObject([
                FloatObject(round(x0, 4)), FloatObject(round(y0, 4)),
                FloatObject(round(x0 + want_w, 4)),
                FloatObject(round(y0 + want_h, 4)),
            ])

    writer.add_page(page)
    with open(pdf, "wb") as fh:
        writer.write(fh)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=None,
                    help="interior page count; the spine follows by "
                         f"Lulu's formula (default {PAGES})")
    ap.add_argument("--spine", type=float, default=None,
                    help="spine width in inches, overriding --pages "
                         f"(default {SPINE_IN} for {PAGES} pages)")
    ap.add_argument("--no-url", action="store_true",
                    help="omit the site URL from the back cover")
    ap.add_argument("-o", "--out", type=Path,
                    default=ART / "claudyssey-wrap.pdf")
    args = ap.parse_args()
    if args.spine is not None and args.pages is not None:
        sys.exit("give --pages or --spine, not both")
    spine = (args.spine if args.spine is not None
             else spine_for(args.pages) if args.pages is not None
             else SPINE_IN)
    build(spine, not args.no_url, args.out)
