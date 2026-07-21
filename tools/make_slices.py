"""Phase 3 setup: split the registry into balanced per-writer work packets.

Reads `index/registry.json` (the full classified registry with citations joined
in), sorts the headwords alphabetically, divides them into N contiguous slices of
roughly equal size, and writes one self-contained work packet per slice to
`index/entries/_worklist-NN.md`. Each packet lists, for every headword the writer
must produce: category, aliases/epithets, the disambiguating note, book coverage,
and the real book.line citations — so a writer never has to invent a reference.

Contiguous alphabetical slices (not round-robin) keep each writer's range clean
and non-overlapping, which is what makes the fan-out conflict-free: every headword
belongs to exactly one slice.

Usage:  python tools/make_slices.py --slices 8
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "index" / "registry.json"
ENTRIES = ROOT / "index" / "entries"
REF_CAP = 50  # show at most this many refs per headword in the packet


def chunk(seq, n):
    """Split seq into n contiguous chunks as evenly as possible."""
    k, m = divmod(len(seq), n)
    out, i = [], 0
    for s in range(n):
        size = k + (1 if s < m else 0)
        out.append(seq[i:i + size])
        i += size
    return out


def fmt_refs(refs):
    if len(refs) <= REF_CAP:
        return ", ".join(refs)
    return ", ".join(refs[:REF_CAP]) + f"  (+{len(refs) - REF_CAP} more; see index/registry.json)"


def packet_md(idx, total, slice_rows):
    first, last = slice_rows[0]["headword"], slice_rows[-1]["headword"]
    L = [
        f"# Phase 3 worklist — slice {idx:02d} of {total}  ({first} … {last})\n",
        f"Write an index entry for **each** of the {len(slice_rows)} headwords below, "
        "in this order. Follow `index/entries/WRITER-BRIEF.md` exactly. Output only the "
        f"entries, to `index/entries/entries-{idx:02d}.md`.\n",
        "Each block gives you everything you need: the canonical headword, its category, "
        "aliases/epithets to fold in, a disambiguating note, and the real citations. "
        "Curate the refs down to the key ones per the brief; do not invent any.\n",
        "---\n",
    ]
    for r in slice_rows:
        L.append(f"### {r['headword']}  ·  {r['cat']}")
        if r["aliases"]:
            L.append(f"- **aliases / epithets:** {r['aliases']}")
        if r["note"]:
            L.append(f"- **note:** {r['note']}")
        L.append(f"- **hits:** {r['count']}  ·  **books:** {', '.join(map(str, r['books']))}")
        L.append(f"- **refs:** {fmt_refs(r['refs'])}")
        L.append("")
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--slices", type=int, default=8)
    args = ap.parse_args(argv)

    rows = json.load(open(REG, encoding="utf-8"))
    rows.sort(key=lambda r: r["headword"].lower())
    ENTRIES.mkdir(parents=True, exist_ok=True)

    slices = chunk(rows, args.slices)
    for i, sl in enumerate(slices, 1):
        (ENTRIES / f"_worklist-{i:02d}.md").write_text(
            packet_md(i, args.slices, sl), encoding="utf-8"
        )
        print(f"slice {i:02d}: {len(sl):>3} headwords  "
              f"{sl[0]['headword']:<16} … {sl[-1]['headword']}")
    print(f"\nwrote {args.slices} worklists to {ENTRIES}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
