"""Split the Perseus TEI XML of the Odyssey into per-book plain-text files.

Each output line is `<line number>\t<Greek text>`. Lines that wrap in the XML
(because of embedded milestone elements) are joined and whitespace-normalized.
"""
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"

src = Path(__file__).parent.parent / "greek" / "tlg0012.tlg002.perseus-grc2.xml"
out_dir = Path(__file__).parent.parent / "greek"

tree = ET.parse(src)
body = tree.getroot().find(f"{TEI}text/{TEI}body/{TEI}div")

total_lines = 0
for book in body.findall(f"{TEI}div[@subtype='book']"):
    book_n = int(book.get("n"))
    lines = []
    for l in book.findall(f".//{TEI}l"):
        text = "".join(l.itertext())
        text = re.sub(r"\s+", " ", text).strip()
        lines.append((l.get("n"), text))
    out = out_dir / f"book-{book_n:02d}.txt"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for n, text in lines:
            f.write(f"{n}\t{text}\n")
    total_lines += len(lines)
    print(f"Book {book_n:2d}: {len(lines):4d} lines -> {out.name}")

print(f"Total: {total_lines} lines")
