"""Phase 3 merge + validation: assemble the writers' slices into one index.

Reads the per-slice worklists (`index/entries/_worklist-NN.md`) for the
authoritative ordered headword list each writer was given, splits each writer's
output (`index/entries/entries-NN.md`) on `---` separators, and aligns them
positionally — so a missing or extra entry surfaces immediately instead of
silently shifting every later entry onto the wrong headword.

Checks:
  * coverage — every worklist headword has exactly one entry, none extra;
  * citations — every `book.line` an entry cites is a real occurrence of that
    headword (from `registry.json`); anything else is flagged for human review
    (advisory: a verified scene-line need not be an occurrence line).

If coverage is clean it writes the merged, alphabetized `index/index.md`.

Usage:  python tools/merge_index.py
"""
import json
import re
import sys
from pathlib import Path

# UTF-8 console for Greek/diacritics.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "index" / "entries"
REG = ROOT / "index" / "registry.json"
OUT = ROOT / "index" / "index.md"

HEADWORD_LINE = re.compile(r"^###\s+(.+?)\s+·\s+", re.MULTILINE)
BOOKLINE = re.compile(r"\b(\d{1,2})\.(\d{1,3})\b")


def worklist_headwords(path):
    """Ordered headwords a worklist assigned (from its '### Name · CAT' blocks)."""
    return HEADWORD_LINE.findall(path.read_text(encoding="utf-8"))


def split_entries(text):
    """Split a writer's file into entry blocks on lines that are exactly '---'."""
    blocks, cur = [], []
    for line in text.splitlines():
        if line.strip() == "---":
            if any(s.strip() for s in cur):
                blocks.append("\n".join(cur).strip())
            cur = []
        else:
            cur.append(line)
    if any(s.strip() for s in cur):
        blocks.append("\n".join(cur).strip())
    return blocks


def main():
    reg = {r["headword"]: r for r in json.load(open(REG, encoding="utf-8"))}
    worklists = sorted(ENTRIES.glob("_worklist-*.md"))
    if not worklists:
        sys.exit("no worklists found — run make_slices.py first")

    merged = {}          # headword -> entry text
    problems = []
    missing_outputs = []

    for wl in worklists:
        n = wl.stem.split("-")[1]
        out = ENTRIES / f"entries-{n}.md"
        heads = worklist_headwords(wl)
        if not out.exists():
            missing_outputs.append(out.name)
            continue
        blocks = split_entries(out.read_text(encoding="utf-8"))
        if len(blocks) != len(heads):
            problems.append(
                f"slice {n}: {len(blocks)} entries for {len(heads)} headwords "
                f"— positional alignment unreliable; fix count first")
        for hw, block in zip(heads, blocks):
            merged[hw] = block
            valid = set(reg.get(hw, {}).get("refs", []))
            cited = {f"{b}.{l}" for b, l in BOOKLINE.findall(block)}
            stray = sorted(cited - valid, key=lambda r: tuple(map(int, r.split("."))))
            if stray:
                problems.append(f"  [{hw}] citations not in occurrence set: {', '.join(stray)}")
        for hw in heads[len(blocks):]:
            problems.append(f"slice {n}: no entry produced for '{hw}'")

    covered = set(merged)
    expected = set(reg)
    missing = sorted(expected - covered)
    extra = sorted(covered - expected)

    print(f"headwords expected: {len(expected)}   covered: {len(covered)}")
    if missing_outputs:
        print(f"\n[!] writer outputs not found yet: {', '.join(missing_outputs)}")
    if missing:
        print(f"\n[!] {len(missing)} headwords with NO entry:\n    " + "  ".join(missing))
    if extra:
        print(f"\n[!] {len(extra)} entries for unknown headwords:\n    " + "  ".join(extra))
    if problems:
        print(f"\n[!] {len(problems)} issues flagged for review:")
        for p in problems:
            print("   ", p)

    clean = not (missing_outputs or missing or extra
                 or any("alignment unreliable" in p or "no entry produced" in p for p in problems))
    if not clean:
        print("\nCoverage not clean — index.md NOT written. Resolve the above, re-run.")
        return 1

    # write merged, alphabetized index
    body = ["# The Odyssey — index of names and places\n",
            "Every named person, god, people, and place in the poem, with epithets, "
            "aliases, kin, and line citations. Generated from `index/entries/` by "
            "`tools/merge_index.py`; see `index/canon.md` for the editorial method.\n"]
    for hw in sorted(merged, key=str.lower):
        body.append(merged[hw])
        body.append("\n---\n")
    OUT.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    print(f"\nOK — wrote {OUT} with {len(merged)} entries"
          + (f" ({len(problems)} advisory citation flags to review)" if problems else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
