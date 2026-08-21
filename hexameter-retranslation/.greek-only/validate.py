"""Validate Greek-only Odyssey drafts before they replace reading texts."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


NUMBERED = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")
WORD = re.compile(r"[^\W_]+(?:[’'][^\W_]+)?", re.UNICODE)
CONTRACTION = re.compile(
    r"\b(?:can['’]t|won['’]t|shan['’]t|ain['’]t|isn['’]t|aren['’]t|"
    r"wasn['’]t|weren['’]t|don['’]t|doesn['’]t|didn['’]t|haven['’]t|"
    r"hasn['’]t|hadn['’]t|couldn['’]t|wouldn['’]t|shouldn['’]t|mustn['’]t|"
    r"I['’](?:m|d|ll|ve)|you['’](?:re|d|ll|ve)|we['’](?:re|d|ll|ve)|"
    r"they['’](?:re|d|ll|ve)|he['’](?:s|d|ll)|she['’](?:s|d|ll)|"
    r"it['’](?:s|d|ll)|there['’]s|that['’]s|what['’]s|who['’]s|let['’]s)\b",
    re.IGNORECASE,
)


def verses(path: Path) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = NUMBERED.match(raw)
        if match:
            result.append((int(match.group(1)), match.group(2)))
    return result


def validate(book: int, root: Path) -> bool:
    greek_path = root / "greek" / f"book-{book:02d}.txt"
    draft_path = root / "hexameter-retranslation" / ".greek-only" / f"book-{book:02d}.md"
    greek = verses(greek_path)
    draft = verses(draft_path)
    expected = [number for number, _ in greek]
    actual = [number for number, _ in draft]
    problems: list[str] = []
    warnings: list[str] = []

    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        duplicates = sorted(number for number, count in Counter(actual).items() if count > 1)
        problems.append(
            f"numbering differs (missing={missing}, extra={extra}, duplicates={duplicates})"
        )

    short = [number for number, text in draft if len(WORD.findall(text)) < 4]
    if short:
        problems.append(f"fewer than four words: {short}")

    contractions = [number for number, text in draft if CONTRACTION.search(text)]
    if contractions:
        problems.append(f"lexical contractions requiring voice review: {contractions}")

    repeated = [
        text
        for text, count in Counter(text.casefold() for _, text in draft).items()
        if count > 2
    ]
    if repeated:
        warnings.append(f"lines repeated more than twice (formula review): {len(repeated)}")

    straight_quotes = [number for number, text in draft if '"' in text]
    if straight_quotes:
        problems.append(f"straight quotation marks: {straight_quotes}")

    word_counts = [len(WORD.findall(text)) for _, text in draft]
    mean_words = sum(word_counts) / len(word_counts) if word_counts else 0
    status = "FAIL" if problems else "PASS"
    print(
        f"Book {book:02d}: {status}; Greek={len(greek)} draft={len(draft)} "
        f"mean_words={mean_words:.2f}"
    )
    for problem in problems:
        print(f"  - {problem}")
    for warning in warnings:
        print(f"  - WARNING: {warning}")
    return not problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("books", nargs="+", type=int)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    results = [validate(book, repo_root) for book in args.books]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
