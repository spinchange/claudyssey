#!/usr/bin/env python3
"""Build the web reading edition: one HTML page per book, into docs/read/.

Reads translation/book-NN.md (untouched) and emits:

    docs/read/read.css        shared stylesheet (matches the landing page theme)
    docs/read/index.html      contents page: all 24 books with their arguments
    docs/read/book-NN.html    one page per book

Each verse line gets an anchor (#L123); every fifth line shows its number in
the gutter. Footnote markers become superscript links to endnotes at the foot
of the page, numbered sequentially within the book; each endnote links back
to its marker and to the verse line it glosses.

Usage:
    python tools/build_web.py
"""
from __future__ import annotations
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translation"
OUT = ROOT / "docs" / "read"

VERSE_RE = re.compile(r"^(\d+)\s+(.*)$")
DEF_RE = re.compile(r"^\[\^L(\d+)\]:\s*(.*)$")
REF_RE = re.compile(r"\[\^L(\d+)\]")
EM_RE = re.compile(r"\*([^*]+)\*")

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI",
         "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
         "XXI", "XXII", "XXIII", "XXIV"]


def inline(text: str) -> str:
    """Escape HTML, then render the one bit of markdown the source uses."""
    return EM_RE.sub(r"<em>\1</em>", html.escape(text, quote=False))


def parse_book(path: Path):
    """Return (argument, stanzas, notes). A stanza is a list of
    (lineno, text) tuples; notes is a list of (lineno, body) in file order."""
    argument = ""
    stanzas: list[list[tuple[int, str]]] = []
    cur: list[tuple[int, str]] = []
    notes: list[tuple[int, str]] = []
    in_notes = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Notes"):
            in_notes = True
            continue
        if in_notes:
            m = DEF_RE.match(line)
            if m:
                notes.append((int(m.group(1)), m.group(2)))
            continue
        if line.startswith("# "):
            continue
        s = line.strip()
        if not s:
            if cur:
                stanzas.append(cur)
                cur = []
            continue
        m = VERSE_RE.match(line)
        if m:
            cur.append((int(m.group(1)), m.group(2)))
        elif s.startswith("*") and s.endswith("*") and not argument:
            argument = s.strip("*")
    if cur:
        stanzas.append(cur)
    return argument, stanzas, notes


def page(title: str, desc: str, body: str, depth_home: str = "../") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="read.css">
</head>
<body>
<div class="meander"></div>
<div class="wrap">
<p class="site"><a href="{depth_home}">The Odyssey · a Claudyssey</a></p>
{body}
</div>
<div class="meander"></div>
<footer>
  <a href="index.html">Contents</a> · <a href="{depth_home}">About &amp; downloads</a><br>
  translation © its author · Greek source public domain
</footer>
</body>
</html>
"""


def booknav(n: int, bottom: bool = False) -> str:
    prev_a = (f'<a href="book-{n-1:02d}.html">&lsaquo; Book {n-1}</a>'
              if n > 1 else "<span></span>")
    next_a = (f'<a href="book-{n+1:02d}.html">Book {n+1} &rsaquo;</a>'
              if n < 24 else "<span></span>")
    cls = "booknav bottom" if bottom else "booknav"
    return (f'<nav class="{cls}">{prev_a}'
            f'<a href="index.html">Contents</a>{next_a}</nav>')


def build_book(n: int) -> str:
    argument, stanzas, notes = parse_book(SRC / f"book-{n:02d}.md")
    # note lineno -> sequential number within the book
    seq = {ln: i + 1 for i, (ln, _) in enumerate(notes)}

    out = [booknav(n)]
    out.append('<header class="bookhead">')
    out.append(f'<h1>Book {ROMAN[n-1]}</h1>')
    if argument:
        out.append(f'<p class="argument">{inline(argument)}</p>')
    out.append("</header>")

    out.append('<div class="verse">')
    for stanza in stanzas:
        out.append('<div class="stanza">')
        for lineno, text in stanza:
            def ref(m: re.Match) -> str:
                i = seq.get(int(m.group(1)))
                if i is None:
                    return ""
                return (f'<a class="fnref" id="r{i}" href="#n{i}">'
                        f'<sup>{i}</sup></a>')
            # substitute markers on the escaped text: the marker pattern
            # contains no characters that html.escape rewrites
            body = REF_RE.sub(ref, inline(text))
            num = (f'<a class="ln" href="#L{lineno}">{lineno}</a>'
                   if lineno % 5 == 0 or lineno == 1 else "")
            out.append(f'<p class="v" id="L{lineno}">{num}{body}</p>')
        out.append("</div>")
    out.append("</div>")

    if notes:
        out.append('<section class="notes">')
        out.append("<h2>Notes</h2>")
        for i, (lineno, body) in enumerate(notes, 1):
            body = REF_RE.sub("", body)  # defensive: no markers inside notes
            out.append(
                f'<p class="note" id="n{i}">'
                f'<span class="nnum">{i}</span> '
                f'<a class="nline" href="#L{lineno}">line {lineno}</a> — '
                f'{inline(body)} '
                f'<a class="back" href="#r{i}" title="back to the text">&#8617;</a></p>')
        out.append("</section>")

    out.append(booknav(n, bottom=True))

    desc = f"Book {n} of the Odyssey, in a line-for-line English translation" \
           + (f": {argument.rstrip('.')}." if argument else ".")
    return page(f"Odyssey, Book {n} — a Claudyssey", desc, "\n".join(out))


def build_contents(arguments: dict[int, str]) -> str:
    out = ['<header class="bookhead"><h1>The Odyssey</h1>',
           '<p class="argument">a line-for-line translation '
           '&middot; twenty-four books</p></header>',
           '<ol class="toc">']
    for n in range(1, 25):
        arg = inline(arguments.get(n, ""))
        out.append(
            f'<li><a href="book-{n:02d}.html"><b>Book {ROMAN[n-1]}</b>'
            f'<span>{arg}</span></a></li>')
    out.append("</ol>")
    return page("Read the Odyssey — a Claudyssey",
                "Homer's Odyssey complete in a line-for-line English "
                "translation with notes: all twenty-four books, free to read "
                "online.", "\n".join(out))


CSS = """\
:root{
  --wine:#46192b; --wine-deep:#1e0b15; --bone:#ead9b4; --gold:#c99b3f;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
html,body{margin:0}
body{
  background:
    radial-gradient(ellipse at 50% 38%, rgba(0,0,0,0) 55%, rgba(12,4,8,.55) 100%),
    linear-gradient(#46192b, #331323 55%, #1e0b15);
  background-attachment:fixed;
  color:var(--bone);
  font-family:"Palatino Linotype","Book Antiqua",Palatino,Georgia,serif;
  line-height:1.55; min-height:100vh;
}
a{color:var(--gold)}
.wrap{max-width:680px; margin:0 auto; padding:0 22px}

.meander{height:26px; background-repeat:repeat-x; background-size:auto 26px;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='40' height='26'><g fill='none' stroke='%23ead9b4' stroke-width='2.6'><path d='M0 4 H40'/><path d='M0 22 H40'/><path d='M28 22 V8 H11 V18 H19'/></g></svg>");
  opacity:.85; margin:14px 0 0}

.site{text-align:center; margin:18px 0 0; font-size:.8rem;
  letter-spacing:.14em; text-transform:uppercase}
.site a{color:var(--bone); opacity:.75; text-decoration:none}
.site a:hover{opacity:1; color:var(--gold)}

.booknav{display:flex; justify-content:space-between; gap:12px;
  margin:20px 0 0; font-size:.92rem}
.booknav.bottom{margin:34px 0 8px; border-top:1px solid rgba(201,155,63,.3);
  padding-top:16px}
.booknav a{text-decoration:none}
.booknav a:hover{text-decoration:underline}
.booknav span{min-width:70px}

.bookhead{text-align:center; margin:26px 0 30px}
.bookhead h1{font-weight:normal; letter-spacing:.12em; font-size:2.1rem;
  margin:0 0 .15em}
.argument{font-style:italic; opacity:.85; margin:0}

.verse{padding-left:2.6rem}
.stanza{margin:0 0 1.15em}
.v{margin:0; position:relative; padding-left:1.4em; text-indent:-1.4em}
.ln{position:absolute; left:-3.4rem; top:.32em; width:2.6rem;
  text-align:right; font-size:.72em; color:var(--gold); opacity:.55;
  text-decoration:none; text-indent:0}
.ln:hover{opacity:1}
.v:target, .note:target{background:rgba(201,155,63,.14); border-radius:3px}
.fnref{text-decoration:none; padding:0 .08em}
.fnref sup{font-size:.68em}

.notes{margin-top:40px; border-top:1px solid rgba(201,155,63,.3);
  padding-top:6px}
.notes h2{font-weight:normal; font-variant:small-caps; letter-spacing:.06em;
  color:var(--gold); font-size:1.25rem}
.note{font-size:.92rem; opacity:.92; margin:0 0 .85em;
  padding-left:1.6em; text-indent:-1.6em}
.nnum{color:var(--gold); font-size:.8em; vertical-align:.25em}
.nline{font-variant:small-caps; text-decoration:none; white-space:nowrap}
.nline:hover{text-decoration:underline}
.back{text-decoration:none}

.toc{list-style:none; margin:0; padding:0}
.toc li{margin:0 0 2px}
.toc a{display:flex; gap:14px; align-items:baseline; padding:9px 12px;
  text-decoration:none; color:var(--bone); border-radius:5px;
  border:1px solid transparent}
.toc a:hover{background:rgba(201,155,63,.1); border-color:rgba(201,155,63,.35)}
.toc b{color:var(--gold); font-weight:normal; letter-spacing:.06em;
  white-space:nowrap; min-width:5.4em}
.toc span{font-style:italic; opacity:.85; font-size:.95rem}

footer{text-align:center; font-size:.8rem; opacity:.7; padding:20px 0 40px}

@media (max-width:560px){
  .wrap{padding:0 14px}
  .verse{padding-left:2.1rem}
  .ln{left:-2.6rem; width:2rem}
  .toc b{min-width:4.6em}
}
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "read.css").write_text(CSS, encoding="utf-8")
    arguments: dict[int, str] = {}
    for n in range(1, 25):
        src = SRC / f"book-{n:02d}.md"
        arguments[n] = parse_book(src)[0]
        (OUT / f"book-{n:02d}.html").write_text(build_book(n), encoding="utf-8")
        print(f"book-{n:02d}.html")
    (OUT / "index.html").write_text(build_contents(arguments), encoding="utf-8")
    print("index.html + read.css")


if __name__ == "__main__":
    main()
