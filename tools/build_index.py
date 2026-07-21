"""Phase 1 of the name index: deterministic occurrence extraction.

Reads the authoritative translation files (translation/book-NN.md), finds every
capitalized token in the *verse body* (never in stage directions, titles, or the
footnote apparatus), and records where each one occurs. Output is a raw
occurrence table — a list of candidate proper names with a citation for every
appearance — which the editorial canonicalization pass (Phase 2) then curates
and resolves into aliases.

This step makes no editorial judgments. It does exactly one non-obvious thing
beyond "find capitalized words": it drops a fixed stoplist of function words and
common line-initial words (And, But, Then, He, ...) so the candidate list isn't
drowned in sentence-openers. Everything dropped is still reported, under a
separate heading, so nothing is silently lost.

Usage:
    python tools/build_index.py                # writes index/occurrences.{json,md}
    python tools/build_index.py --min 3        # table shows names with >=3 hits
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translation"
OUT = ROOT / "index"

# A verse line is "<number><whitespace><text>". Footnote definitions ("[^L12]:")
# and the italic stage-direction / title lines never start with a bare number,
# so this pattern already excludes them.
VERSE = re.compile(r"^(\d+)\s+(.*)$")

# Inline footnote markers like "driven[^L1]" — stripped before tokenizing so the
# marker never fuses onto the preceding word.
FOOTREF = re.compile(r"\[\^[^\]]*\]")

# A word is a run of letters (incl. accented ones); we keep the first letter's
# case to decide whether it's a candidate name.
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# Common capitalized words that occur mainly as sentence/line openers or as
# generic address, not as proper names. Dropped from the candidate table (but
# reported separately). Kept deliberately conservative: when in doubt, a token
# stays IN the candidate list for the human curator to reject, rather than being
# hidden here.
STOP = {
    # pronouns / determiners / conjunctions / prepositions
    "A", "And", "As", "At", "But", "By", "For", "From", "He", "Her", "Here",
    "His", "How", "I", "If", "In", "It", "Its", "Me", "My", "No", "Nor", "Not",
    "Now", "O", "Of", "Oh", "On", "Or", "Our", "Out", "She", "So", "Some",
    "Such", "That", "The", "Their", "Them", "Then", "There", "These", "They",
    "This", "Those", "Thus", "To", "Up", "We", "What", "When", "Where", "Which",
    "While", "Who", "Whom", "Why", "With", "You", "Your", "Yet",
    # common verbs/adverbs that open imperative or exclamatory lines
    "Ah", "Alas", "Away", "Be", "Come", "Do", "Down", "Even", "Ever", "Give",
    "Go", "Good", "Hear", "Just", "Know", "Let", "Like", "Long", "Look", "May",
    "Much", "Nay", "Never", "Off", "Once", "Only", "Over", "Say", "See", "Since",
    "Still", "Take", "Tell", "Well", "Would",
    # generic relational / vocative nouns (people are named, these are roles)
    "Dear", "Father", "Friend", "King", "Lady", "Lord", "Man", "Master",
    "Men", "Mother", "Queen", "Sir", "Son", "Stranger", "Wife",
}


def book_number(path):
    m = re.search(r"book-(\d+)", path.name)
    return int(m.group(1)) if m else 0


def normalize_token(word):
    """Return a candidate name token, or None.

    Keeps only capitalized words. Trims a trailing possessive that the WORD
    regex would already have split off, so this is mostly a case test; the
    possessive handling matters for tokens the regex kept whole in odd cases.
    """
    if not word or not word[0].isupper():
        return None
    return word


def scan():
    # name -> list of "book.line" refs (with duplicates if a name repeats on a line)
    refs = defaultdict(list)
    files = sorted(SRC.glob("book-*.md"), key=book_number)
    if not files:
        sys.exit(f"no translation files found under {SRC}")
    for path in files:
        b = book_number(path)
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = VERSE.match(raw)
            if not m:
                continue
            line_no, text = m.group(1), m.group(2)
            text = FOOTREF.sub(" ", text)
            for word in WORD.findall(text):
                tok = normalize_token(word)
                if tok:
                    refs[tok].append(f"{b}.{line_no}")
    return refs


def summarize(refs):
    """name -> {count, books, refs} with refs de-duplicated and sorted."""
    def key(ref):
        b, l = ref.split(".")
        return (int(b), int(l))

    out = {}
    for name, rlist in refs.items():
        uniq = sorted(set(rlist), key=key)
        books = sorted({int(r.split(".")[0]) for r in rlist})
        out[name] = {"count": len(rlist), "books": books, "refs": uniq}
    return out


def write_json(data):
    OUT.mkdir(exist_ok=True)
    ordered = dict(sorted(data.items(), key=lambda kv: (-kv[1]["count"], kv[0])))
    (OUT / "occurrences.json").write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def fmt_books(books):
    """Compress a sorted book list into ranges: [1,2,3,5] -> '1-3, 5'."""
    if not books:
        return ""
    parts, start, prev = [], books[0], books[0]
    for b in books[1:]:
        if b == prev + 1:
            prev = b
            continue
        parts.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = b
    parts.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(parts)


def write_md(data, min_count):
    candidates = {n: d for n, d in data.items() if n not in STOP}
    dropped = {n: d for n, d in data.items() if n in STOP}

    def rows(items):
        items = sorted(items, key=lambda kv: (-kv[1]["count"], kv[0]))
        lines = ["| name | hits | books |", "| --- | ---: | --- |"]
        for name, d in items:
            lines.append(f"| {name} | {d['count']} | {fmt_books(d['books'])} |")
        return "\n".join(lines)

    shown = [(n, d) for n, d in candidates.items() if d["count"] >= min_count]
    tail = [(n, d) for n, d in candidates.items() if d["count"] < min_count]

    md = []
    md.append("# Name index — Phase 1 occurrence table\n")
    md.append(
        "Generated by `tools/build_index.py` from `translation/`. This is raw "
        "extraction, not an edited index: tokens are single capitalized words, "
        "aliases are NOT yet merged, and no judgment has been applied beyond a "
        "function-word stoplist. Full per-occurrence citations live in "
        "`index/occurrences.json`.\n"
    )
    md.append(f"**{len(candidates)}** candidate names "
              f"(**{len(shown)}** with ≥{min_count} hits). "
              f"**{len(dropped)}** stoplisted tokens hidden below.\n")
    md.append(f"## Candidate names (≥{min_count} occurrences)\n")
    md.append(rows(shown))
    md.append(f"\n## Long tail (< {min_count} occurrences)\n")
    md.append(rows(tail))
    md.append("\n## Stoplisted tokens (dropped as function/relational words)\n")
    md.append(rows(list(dropped.items())))
    (OUT / "occurrences.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=3,
                    help="minimum hits to appear in the main table (default 3)")
    args = ap.parse_args(argv)

    refs = scan()
    data = summarize(refs)
    write_json(data)
    write_md(data, args.min)
    total = sum(d["count"] for d in data.values())
    cands = sum(1 for n in data if n not in STOP)
    print(f"scanned {len(list(SRC.glob('book-*.md')))} books")
    print(f"{len(data)} distinct capitalized tokens, {total} total occurrences")
    print(f"{cands} candidate names after stoplist")
    print(f"wrote {OUT/'occurrences.json'} and {OUT/'occurrences.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
