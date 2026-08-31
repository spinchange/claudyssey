#!/usr/bin/env python3
"""Draw the map of the Odyssey's locatable places as a black-ink SVG.

Editorial rule: only places the poem names that have a location on the
ground are plotted. The fabulous geography (Ogygia, Aeaea, Scheria,
Aeolia, the Cyclopes, the Laestrygonians, the Lotus-eaters, Thrinacia)
is not shown, and the caption says so.

Two panels on one upright page, each the width of the text block:
  * the Greek world, Ithaca to the Troad, at a scale that can hold the
    crowded Ionian and Peloponnesian names;
  * beneath it a strip of the wider sea from Sicily to Phoenicia and
    the Nile delta, for the places the poem names at a distance, with a
    box marking the extent of the panel above.
An Ithaca inset (INSET below) exists in the code but is switched off.

Data and rights:
  * Coast, rivers, and lakes: Natural Earth 1:10m (public domain).
    The three GeoJSON files are vendored in art/natural-earth/ (see its
    README); --data-dir points elsewhere if needed:
        ne_10m_land.geojson
        ne_10m_rivers_lake_centerlines.geojson
        ne_10m_lakes.geojson
  * Place coordinates: hand-entered, then checked against Pleiades
    (pleiades.stoa.org, CC BY) on 2026-08-25. The record of that check,
    with each place's Pleiades id and the distance between the two
    coordinates, is art/map-places.tsv. Point features sit on their
    Pleiades representative point; region and island names are label
    positions, not points; the Ithacan features of the inset have no
    Pleiades entries and follow the traditional identifications.

Projection: plain equirectangular with the x-axis scaled by cos(36 N),
accurate enough over these latitudes and trivially invertible.

Usage:
    python tools/build_map.py --data-dir <dir with the geojson>

The output, art/map.svg, is placed by tools/build_print.py on the verso
facing the opening of Book 1.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

PT = 72.0
BLOCK_W_IN = 4.18            # the 6x9 text block's width
COS = math.cos(math.radians(36.0))

# ----------------------------------------------------------------- places
# (name, lat, lon, kind, dx, dy, anchor)
#   kind: city | island | region | cape | mountain | sea
#   dx, dy: label offset in points from the point; anchor: start|middle|end
GREECE = [
    # Ithaca and the west
    ("Ithaca",        38.42, 20.68, "island",  -9,  -4, "end"),
    ("Same",          38.20, 20.62, "island", -12,   6, "end"),
    ("Zacynthus",     37.78, 20.85, "island",   0,  11, "middle"),
    ("Dodona",        39.55, 20.79, "city",     4,   2, "start"),
    ("Ephyra",        39.24, 20.53, "city",    -4,  -5, "end"),
    ("Thesprotia",    39.78, 20.45, "region",   0,   0, "middle"),
    ("Elis",          37.89, 21.38, "city",     4,   0, "start"),
    ("Pylos",         37.03, 21.70, "city",    -4,   3, "end"),
    ("Pherae",        37.04, 22.11, "city",     3,   8, "start"),
    ("Sparta",        37.08, 22.43, "city",     4,   0, "start"),
    ("Achaea",        38.13, 22.00, "region",   0,   0, "middle"),
    ("Mycenae",       37.73, 22.76, "city",     4,  -5, "start"),
    ("Argos",         37.63, 22.73, "city",     4,   7, "start"),
    ("Malea",         36.450,23.202,"cape",     4,   3, "start"),
    ("Cythera",       36.22, 22.98, "island",   0,   9, "middle"),
    ("Parnassus",     38.53, 22.62, "mountain", 0,  -4, "middle"),
    ("Thebes",        38.32, 23.32, "city",     4,   3, "start"),
    ("Athens",        37.97, 23.73, "city",     4,   0, "start"),
    ("Sunium",        37.65, 24.02, "cape",     4,   4, "start"),
    ("Euboea",        38.85, 23.55, "island",   0,   0, "middle"),
    ("Geraestus",     37.977,24.538,"cape",     5,   7, "start"),
    ("Scyros",        38.90, 24.55, "island",   5,   2, "start"),
    ("Delos",         37.40, 25.27, "island",   5,   2, "start"),
    ("Iolcus",        39.366,22.969,"city",     4,   0, "start"),
    # the north Aegean and the Troad
    ("Ismarus",       40.874,25.511,"city",     0,  10, "middle"),   # = Maroneia
    ("Cicones",       41.10, 25.30, "region",   0,   0, "middle"),
    ("Lemnos",        39.90, 25.20, "island",  -5,   0, "end"),
    ("Troy",          39.96, 26.24, "city",     4,  -1, "start"),
    ("Tenedos",       39.83, 26.07, "island",  -5,   4, "end"),
    ("Lesbos",        39.20, 26.30, "island",   0,   3, "middle"),
    ("Psyra",         38.55, 25.57, "island",  -4,  -2, "end"),
    ("Chios",         38.40, 26.05, "island",   0,  15, "middle"),
    # Crete
    ("Crete",         35.15, 24.10, "region",   0,   0, "middle"),
    ("Cnossus",       35.30, 25.16, "city",     4,  -1, "start"),
    ("Phaestus",      35.05, 24.81, "city",     0,   8, "middle"),
]

WIDER = [
    ("Ithaca",        38.42, 20.68, "city",    -3,   0, "end"),
    ("Troy",          39.96, 26.24, "city",     3,   0, "start"),
    ("Crete",         34.70, 24.60, "region",   0,   0, "middle"),
    ("Sicily",        37.50, 14.95, "region",   0,   0, "middle"),
    ("Temesa (?)",    39.036,16.160,"city",     3,   0, "start"),
    ("Libya",         31.80, 21.00, "region",   0,   0, "middle"),
    ("Pharos",        31.21, 29.88, "city",    -3,  -1, "end"),
    ("Egypt",         31.85, 26.00, "region",   0,   0, "middle"),
    ("Cyprus",        35.05, 33.20, "region",   0,   0, "middle"),
    ("Paphos",        34.705,32.579,"city",    -2,   5, "end"),   # Palaepaphos, the sanctuary of 8.362
    ("Sidon",         33.56, 35.37, "city",    -3,   0, "end"),
    ("Phoenicia",     33.90, 35.00, "region",  -2,   0, "end"),
]

# Ithaca, with the traditional identifications. The poem's Ithacan
# topography does not fit the modern island cleanly (9.25-26 is the
# crux), which is why the Paliki hypothesis exists; the drawing follows
# the tradition that the ancients themselves attested at the Polis cave,
# and the caption says that a rival theory exists.
# An eighth element (label_lat, label_lon) places the label absolutely, in
# the open sea east of the island, with a leader line back to the feature.
E = 20.74
ITHACA = [
    ("School of Homer", 38.46, 20.63, "site",   0, 0, "start", (38.485, E)),
    ("Polis Bay",       38.435,20.615,"bay",    0, 0, "start", (38.452, E)),
    ("Mt Neriton",      38.42, 20.66, "mountain",0,0, "start", (38.419, E)),
    ("Phorcys' harbor", 38.375,20.700,"bay",    0, 0, "start", (38.386, E)),
    ("Nymphs' cave",    38.36, 20.705,"site",   0, 0, "start", (38.353, E)),
    ("Arethusa",        38.33, 20.73, "site",   0, 0, "start", (38.320, E)),
    ("Asteris",         38.385,20.585,"islet", -3, 6, "end"),
    ("Same",            38.25, 20.65, "city",   4, 2, "start"),
    ("Cephallenia",     38.42, 20.475,"region-v",0, 0, "middle"),
    ("Ithaca",          38.215,20.86, "region", 0, 0, "middle"),
]

# The Ithaca inset is switched off: at Natural Earth's resolution the
# island is a featureless blob, and squeezing it beside the wider strip
# crowded both. The data and the layout are kept should a hand-traced
# coastline ever make it worth a figure of its own (facing Book 13 would be
# the place, not this page).
INSET = False

PANELS = {
    # name: extent, places, font scale, river rank cutoff, width in inches
    "greece": dict(lon=(19.3, 27.2), lat=(34.8, 41.4), places=GREECE,
                   font=1.0, rivers=7, width=BLOCK_W_IN),
    "wider":  dict(lon=(13.0, 36.4), lat=(31.0, 41.0), places=WIDER,
                   font=0.8 if INSET else 0.9, rivers=5,
                   width=2.69 if INSET else BLOCK_W_IN),
    "ithaca": dict(lon=(20.44, 20.95), lat=(38.19, 38.53), places=ITHACA,
                   font=0.77, rivers=99, width=1.38),
}
for _n, _p in PANELS.items():
    _p["name"] = _n

# Caption lines. Kept short: the SVG viewport clips at the block width and
# calibre's renderer honours neither clipPath nor overflow, so a line that
# is too long is simply cut off in print.
CAPTION_LINES = [
    "Places named in the Odyssey that can be located.",
    "The fabulous geography of Books 9 to 12 is not shown.",
] + ([
    "Ithaca is drawn with the traditional identifications;",
    "some place Homer's Ithaca on the Paliki peninsula of Cephallenia.",
] if INSET else [])
CREDIT = "Coastlines: Natural Earth (public domain)."

# --------------------------------------------------------------- geometry
def clip_ring(ring, box):
    """Sutherland-Hodgman: clip a polygon ring to a lon/lat rectangle.

    The Eurasian and African mainland polygons run to hundreds of
    thousands of vertices; without clipping every one of them is written
    into the SVG for the sake of the stretch of coast inside the frame.
    """
    x0, y0, x1, y1 = box

    def inside(p, edge):
        return {0: p[0] >= x0, 1: p[0] <= x1, 2: p[1] >= y0, 3: p[1] <= y1}[edge]

    def intersect(a, b, edge):
        (ax, ay), (bx, by) = a, b
        if edge in (0, 1):
            x = x0 if edge == 0 else x1
            t = (x - ax) / (bx - ax)
            return (x, ay + t * (by - ay))
        y = y0 if edge == 2 else y1
        t = (y - ay) / (by - ay)
        return (ax + t * (bx - ax), y)

    pts = [tuple(p[:2]) for p in ring]
    for edge in range(4):
        if not pts:
            break
        out = []
        prev = pts[-1]
        for cur in pts:
            if inside(cur, edge):
                if not inside(prev, edge):
                    out.append(intersect(prev, cur, edge))
                out.append(cur)
            elif inside(prev, edge):
                out.append(intersect(prev, cur, edge))
            prev = cur
        pts = out
    return pts


def clip_line(line, box):
    """Split a polyline into the pieces that lie inside the rectangle."""
    x0, y0, x1, y1 = box
    pieces, cur = [], []
    for lon, lat, *_ in line:
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            cur.append((lon, lat))
        elif cur:
            pieces.append(cur); cur = []
    if cur:
        pieces.append(cur)
    return [pc for pc in pieces if len(pc) > 1]


def bbox_touches(coords, box) -> bool:
    lons = [p[0] for p in coords]; lats = [p[1] for p in coords]
    return not (max(lons) < box[0] or min(lons) > box[2]
                or max(lats) < box[1] or min(lats) > box[3])


class Panel:
    def __init__(self, spec: dict, width_pt: float):
        self.spec = spec
        self.lon0, self.lon1 = spec["lon"]
        self.lat0, self.lat1 = spec["lat"]
        self.w = width_pt
        self.scale = width_pt / ((self.lon1 - self.lon0) * COS)   # pt per degree lat
        self.h = (self.lat1 - self.lat0) * self.scale
        # Geometry is clipped to the frame plus a hair, in degrees worth of
        # 0.3pt at this panel's scale. calibre's PDF renderer ignores SVG
        # clipPath, so the drawing must never rely on it: whatever is
        # emitted is what prints, and the frame stroke (0.5pt) covers the
        # overrun.
        pad_lat = 0.3 / self.scale
        pad_lon = pad_lat / COS
        self.box = (self.lon0 - pad_lon, self.lat0 - pad_lat,
                    self.lon1 + pad_lon, self.lat1 + pad_lat)

    def xy(self, lon, lat):
        return ((lon - self.lon0) * COS * self.scale, (self.lat1 - lat) * self.scale)

    def path(self, pts, close=False):
        d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (self.xy(*p) for p in pts))
        return d + ("Z" if close else "")

    def polys(self, features):
        out = []
        for f in features:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                if not bbox_touches(poly[0], self.box):
                    continue
                d = []
                for ring in poly:
                    pts = clip_ring(ring, self.box)
                    if len(pts) >= 3:
                        d.append(self.path(pts, close=True))
                if d:
                    out.append("".join(d))
        return out

    def lines(self, features, max_rank):
        out = []
        for f in features:
            if (f["properties"].get("scalerank") or 99) > max_rank:
                continue
            g = f["geometry"]
            lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            for ln in lines:
                if not bbox_touches(ln, self.box):
                    continue
                for piece in clip_line(ln, self.box):
                    out.append(self.path(piece))
        return out

    def render(self, land, lakes, rivers, ox, oy, insets=()) -> list[str]:
        fs = self.spec["font"]
        name = self.spec["name"]
        s = [f'<g transform="translate({ox:.1f},{oy:.1f})">',
             f'<clipPath id="clip-{name}"><rect x="0" y="0" width="{self.w:.1f}" height="{self.h:.1f}"/></clipPath>',
             f'<rect x="0" y="0" width="{self.w:.1f}" height="{self.h:.1f}" fill="#e4e4e4"/>',
             f'<g clip-path="url(#clip-{name})">',
             '<g fill="#fff" stroke="#000" stroke-width="0.45" stroke-linejoin="round">',
             *[f'<path d="{d}"/>' for d in self.polys(land)],
             "</g>",
             '<g fill="#e4e4e4" stroke="#000" stroke-width="0.3">',
             *[f'<path d="{d}"/>' for d in self.polys(lakes)],
             "</g>",
             '<g fill="none" stroke="#000" stroke-width="0.3" stroke-opacity="0.5">',
             *[f'<path d="{d}"/>' for d in self.lines(rivers, self.spec["rivers"])],
             "</g>"]
        for other in insets:
            # dashed box marking the extent of another panel
            (a, b), (c, d) = other.spec["lon"], other.spec["lat"]
            x0, y0 = self.xy(a, d); x1, y1 = self.xy(b, c)
            s.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" '
                     'fill="none" stroke="#000" stroke-width="0.6" stroke-dasharray="2,1.5"/>')
        for name_, lat, lon, kind, dx, dy, anchor, *label_at in self.spec["places"]:
            x, y = self.xy(lon, lat)
            f7, f65, f8 = 7 * fs, 6.5 * fs, 7.5 * fs
            if label_at:
                # absolute label position with a leader line from the feature
                lx, ly = self.xy(label_at[0][1], label_at[0][0])
                s.append(f'<path d="M{x:.1f},{y:.1f}L{lx-1.5:.1f},{ly:.1f}" stroke="#000" stroke-width="0.35" fill="none"/>')
                dx, dy = lx - x, ly - y
            if kind in ("bay", "site", "islet") or (label_at and kind == "mountain"):
                # inset-scale features: an open ring for a bay or islet, a
                # small square for a site, roman label
                if kind == "site":
                    s.append(f'<rect x="{x-1.4:.1f}" y="{y-1.4:.1f}" width="2.8" height="2.8" fill="#000"/>')
                elif kind == "mountain":
                    s.append(f'<path d="M{x-2.2:.1f},{y+1.6:.1f}L{x:.1f},{y-2.2:.1f}L{x+2.2:.1f},{y+1.6:.1f}Z" fill="#000"/>')
                else:
                    s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="#fff" stroke="#000" stroke-width="0.6"/>')
                style = ' font-style="italic"' if kind in ("islet", "mountain") else ""
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy+2.2:.1f}" font-size="{f65}"{style} text-anchor="{anchor}">{name_}</text>')
            elif kind == "city":
                s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{1.5*fs:.2f}" fill="#000"/>')
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy+2.4:.1f}" font-size="{f7}" text-anchor="{anchor}">{name_}</text>')
            elif kind == "island":
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy+2.4:.1f}" font-size="{f7}" font-style="italic" text-anchor="{anchor}">{name_}</text>')
            elif kind == "cape":
                s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.1" fill="none" stroke="#000" stroke-width="0.5"/>')
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy+2.4:.1f}" font-size="{f65}" font-style="italic" text-anchor="{anchor}">C. {name_}</text>')
            elif kind == "mountain":
                s.append(f'<path d="M{x-2.2:.1f},{y+1.6:.1f}L{x:.1f},{y-2.2:.1f}L{x+2.2:.1f},{y+1.6:.1f}Z" fill="#000"/>')
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy-2:.1f}" font-size="{f65}" font-style="italic" text-anchor="{anchor}">Mt {name_}</text>')
            elif kind == "region":
                s.append(f'<text x="{x+dx:.1f}" y="{y+dy+2.4:.1f}" font-size="{f8}" letter-spacing="{1.6*fs:.1f}" text-anchor="{anchor}">{name_.upper()}</text>')
            elif kind == "region-v":
                # a region label set vertically, reading upward
                s.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{f8}" letter-spacing="{1.6*fs:.1f}" text-anchor="middle" '
                         f'transform="rotate(-90 {x:.1f} {y:.1f})">{name_.upper()}</text>')
        # scale bar: 100 km, or 300 km on the small-scale strip, or 5 km on
        # the island inset
        bar = 100 / 111.0 * self.scale
        km = 100
        if bar < 20:
            bar *= 3; km = 300
        elif bar > self.w / 2:
            bar /= 20; km = 5
        bx, by = 10.0, self.h - 10.0
        s.append(f'<path d="M{bx:.1f},{by:.1f}h{bar:.1f}M{bx:.1f},{by-2.5:.1f}v5M{bx+bar:.1f},{by-2.5:.1f}v5" stroke="#000" stroke-width="0.6" fill="none"/>')
        s.append(f'<text x="{bx+bar/2:.1f}" y="{by-4:.1f}" font-size="6" text-anchor="middle">{km} km</text>')
        s.append("</g>")   # clip
        s.append(f'<rect x="0.25" y="0.25" width="{self.w-0.5:.1f}" height="{self.h-0.5:.1f}" fill="none" stroke="#000" stroke-width="0.5"/>')
        s.append("</g>")
        return s


def build(data_dir: Path) -> str:
    land = json.loads((data_dir / "ne_10m_land.geojson").read_text(encoding="utf-8"))["features"]
    rivers = json.loads((data_dir / "ne_10m_rivers_lake_centerlines.geojson").read_text(encoding="utf-8"))["features"]
    lakes = json.loads((data_dir / "ne_10m_lakes.geojson").read_text(encoding="utf-8"))["features"]

    W = BLOCK_W_IN * PT
    greece, wider, ithaca = (Panel(PANELS[n], PANELS[n]["width"] * PT)
                             for n in ("greece", "wider", "ithaca"))
    gap = 8.0
    cap_h = 8.0 * len(CAPTION_LINES) + 16.0
    # Layout: the Greek world full width on top; beneath it the wider strip,
    # alone at full width or (INSET) beside the Ithaca inset, their widths
    # summing to the block.
    if INSET:
        assert abs(wider.w + gap + ithaca.w - W) < 1.0, (wider.w, ithaca.w, W)
    row_h = max(wider.h, ithaca.h) if INSET else wider.h
    H = greece.h + gap + row_h + cap_h
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}pt" height="{H:.1f}pt" '
         f'viewBox="0 0 {W:.1f} {H:.1f}" font-family="Gentium, Gentium Plus, Georgia, serif">',
         f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="#fff"/>']
    s += greece.render(land, lakes, rivers, 0, 0, insets=[ithaca] if INSET else [])
    s += wider.render(land, lakes, rivers, 0, greece.h + gap, insets=[greece])
    if INSET:
        s += ithaca.render(land, lakes, rivers, wider.w + gap, greece.h + gap)
    y = greece.h + gap + row_h + 11
    for i, line in enumerate(CAPTION_LINES):
        s.append(f'<text x="{W/2:.1f}" y="{y + 8*i:.1f}" font-size="6" font-style="italic" text-anchor="middle">{line}</text>')
    s.append(f'<text x="{W/2:.1f}" y="{y + 8*len(CAPTION_LINES) + 1:.1f}" font-size="5.6" text-anchor="middle">{CREDIT}</text>')
    s.append("</svg>")
    print(f"greece {greece.w/PT:.2f} x {greece.h/PT:.2f} in; wider {wider.w/PT:.2f} x {wider.h/PT:.2f} in; "
          + (f"ithaca {ithaca.w/PT:.2f} x {ithaca.h/PT:.2f} in; " if INSET else "")
          + f"page {W/PT:.2f} x {H/PT:.2f} in")
    return "\n".join(s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path,
                    default=Path(__file__).resolve().parent.parent / "art" / "natural-earth")
    ap.add_argument("--out", type=Path, default=Path("art/map.svg"))
    a = ap.parse_args()
    svg = build(a.data_dir)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(svg, encoding="utf-8")
    print(f"wrote {a.out} ({len(svg):,} chars)")


if __name__ == "__main__":
    main()
