#!/usr/bin/env python3
"""Build the web reading edition: one HTML page per book, into docs/read/.

Reads translation/book-NN.md (untouched) and emits:

    docs/read/read.css        shared stylesheet (matches the landing page theme)
    docs/read/index.html      contents page: all 24 books with their arguments
    docs/read/book-NN.html    one page per book
    docs/read/names.html      index of names & places, from index/index.md

Each verse line gets an anchor (#L123); every fifth line shows its number in
the gutter. Footnote markers become superscript links to endnotes at the foot
of the page, numbered sequentially within the book; each endnote links back
to its marker and to the verse line it glosses.

names.html renders every entry of index/index.md with its line citations
turned into deep links (12.184 -> book-12.html#L184), plus client-side
category chips, an A-Z bar, and a live name filter.

docs/api/ is a machine-readable mirror for LLMs and scripts that fetch the
site: registry.json (the name index with refs), book-NN.txt (each book's
translation source, verbatim), and manifest.json describing all of it.

Book pages and names.html carry data-pagefind-body so the site search covers
exactly the poem, the notes, and the index. After building, refresh the
search bundle with:

    npx -y pagefind --site docs

Usage:
    python tools/build_web.py
"""
from __future__ import annotations
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translation"
IDX = ROOT / "index" / "index.md"
REGISTRY = ROOT / "index" / "registry.json"
OUT = ROOT / "docs" / "read"
OUT_API = ROOT / "docs" / "api"
SITE = "https://theclaudyssey.com"

VERSE_RE = re.compile(r"^(\d+)\s+(.*)$")
DEF_RE = re.compile(r"^\[\^L(\d+)\]:\s*(.*)$")
REF_RE = re.compile(r"\[\^L(\d+)\]")
EM_RE = re.compile(r"\*([^*]+)\*")
STRONG_RE = re.compile(r"\*\*([^*]+)\*\*")
# entry headline: **Headword** (Greek) · CAT — *Say:* pro-nun-see-AY-shun
ENTRY_HEAD_RE = re.compile(
    r"^\*\*(.+?)\*\*\s*(?:\((.*?)\))?\s*·\s*(\w+)(?:\s*—\s*\*Say:\*\s*(.+))?$")
# a book.line citation anywhere in entry prose, book bounded to 1-24
CITE_RE = re.compile(r"\b(2[0-4]|1[0-9]|[1-9])\.([1-9]\d{0,2})\b")

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


def css_version() -> str:
    """Short content hash of the stylesheet, used to cache-bust the CSS link."""
    return hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]


def page(title: str, desc: str, body: str, depth_home: str = "../",
         indexed: bool = False, head_extra: str = "") -> str:
    body_attr = " data-pagefind-body" if indexed else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="read.css?v={css_version()}">
{head_extra}</head>
<body>
<div class="meander"></div>
<div class="wrap"{body_attr}>
<p class="site" data-pagefind-ignore><a href="{depth_home}">The Odyssey · a Claudyssey</a></p>
{body}
</div>
<div class="meander"></div>
<footer>
  <a href="index.html">Contents</a> · <a href="names.html">Index</a> · <a href="{depth_home}">About &amp; downloads</a><br>
  translation <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a> (public domain) ·
  notes &amp; index © 2026 Chris Duffy, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> ·
  Greek source public domain
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
    return (f'<nav class="{cls}" data-pagefind-ignore>{prev_a}'
            f'<span class="mid"><a href="index.html">Contents</a> · '
            f'<a href="names.html">Index</a></span>{next_a}</nav>')


def build_book(n: int) -> str:
    argument, stanzas, notes = parse_book(SRC / f"book-{n:02d}.md")
    # note lineno -> sequential number within the book
    seq = {ln: i + 1 for i, (ln, _) in enumerate(notes)}

    out = [booknav(n)]
    out.append('<header class="bookhead">')
    out.append(f'<h1 data-pagefind-meta="title">Book {ROMAN[n-1]}</h1>')
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
    return page(f"Odyssey, Book {n} — a Claudyssey", desc, "\n".join(out),
                indexed=True)


SEARCH_HEAD = '<link rel="stylesheet" href="../pagefind/pagefind-ui.css">\n'

SEARCH_BLOCK = """\
<div id="search"></div>
<script src="../pagefind/pagefind-ui.js"></script>
<script>
window.addEventListener('DOMContentLoaded', function () {
  if (window.PagefindUI) new PagefindUI({
    element: '#search', showSubResults: true, showImages: false,
    translations: { placeholder: 'Search the poem, the notes, and the index\\u2026' }
  });
});
</script>"""


def build_contents(arguments: dict[int, str]) -> str:
    out = ['<header class="bookhead"><h1>The Odyssey</h1>',
           '<p class="argument">a line-for-line translation '
           '&middot; twenty-four books</p></header>',
           SEARCH_BLOCK,
           '<ol class="toc">']
    for n in range(1, 25):
        arg = inline(arguments.get(n, ""))
        out.append(
            f'<li><a href="book-{n:02d}.html"><b>Book {ROMAN[n-1]}</b>'
            f'<span>{arg}</span></a></li>')
    out.append("</ol>")
    out.append(
        '<p class="apparatus"><a href="names.html">Index of names &amp; places</a>'
        ' — every person, god, people, and place in the poem, with '
        'pronunciations and linked citations.</p>')
    return page("Read the Odyssey — a Claudyssey",
                "Homer's Odyssey complete in a line-for-line English "
                "translation with notes: all twenty-four books, free to read "
                "online.", "\n".join(out), head_extra=SEARCH_HEAD)


# ---------------------------------------------------------------------------
# Index of names & places (names.html), from index/index.md


def slugify(headword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", headword.lower()).strip("-")


def cite_links(escaped: str) -> str:
    """Turn book.line citations in already-escaped/formatted text into links."""
    return CITE_RE.sub(
        lambda m: (f'<a class="cite" href="book-{int(m.group(1)):02d}.html'
                   f'#L{m.group(2)}">{m.group(1)}.{m.group(2)}</a>'),
        escaped)


def entry_inline(text: str) -> str:
    """Escape, render **strong** / *em*, then link citations."""
    out = html.escape(text, quote=False)
    out = STRONG_RE.sub(r"<strong>\1</strong>", out)
    out = EM_RE.sub(r"<em>\1</em>", out)
    return cite_links(out)


CAT_LABEL = {"MORTAL": "mortal", "GOD": "god", "PEOPLE": "people",
             "PLACE": "place", "OTHER": "other"}
CAT_CHIPS = [("", "All"), ("MORTAL", "Mortals"), ("GOD", "Gods"),
             ("PEOPLE", "Peoples"), ("PLACE", "Places"), ("OTHER", "Other")]


def parse_index_entries():
    """Return entries as dicts; index.md blocks are separated by --- rules."""
    entries = []
    for block in IDX.read_text(encoding="utf-8").split("\n---\n"):
        lines = [ln.rstrip() for ln in block.strip().splitlines()]
        head = next(((i, m) for i, ln in enumerate(lines)
                     if (m := ENTRY_HEAD_RE.match(ln))), None)
        if head is None:  # the file preamble carries no entry headline
            continue
        i, m = head
        headword, greek, cat, say = m.groups()
        entries.append({
            "headword": headword, "greek": greek or "", "cat": cat,
            "say": say or "", "slug": slugify(headword),
            "rest": [ln for ln in lines[i + 1:] if ln.strip()],
        })
    slugs = [e["slug"] for e in entries]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise SystemExit(f"duplicate index slugs: {sorted(dupes)}")
    return entries


# see-also spellings that differ from the entry headword
SEE_ALSO_SPELLING = {"Pirithous": "Peirithous"}


def resolve_see_also(name: str, by_headword: dict[str, str]) -> str | None:
    """Slug for a see-also target: exact headword, headword without a
    parenthetical qualifier ("Hades (underworld)"), or a spelling variant."""
    name = SEE_ALSO_SPELLING.get(name, name)
    slug = by_headword.get(name)
    if slug is None:
        slug = by_headword.get(name.split(" (")[0])
    return slug


def render_entry(e: dict, by_headword: dict[str, str]) -> str:
    # filter key: headword, greek, and any "Also called" aliases
    also = next((ln for ln in e["rest"] if ln.startswith("*Also called:*")), "")
    key = html.escape(f'{e["headword"]} {e["greek"]} {also}'.lower(), quote=True)
    out = [f'<article class="entry" id="{e["slug"]}" data-cat="{e["cat"]}" '
           f'data-key="{key}">']
    grc = (f' <span class="grc" lang="grc">{html.escape(e["greek"], quote=False)}</span>'
           if e["greek"] else "")
    out.append(f'<h3>{html.escape(e["headword"], quote=False)}{grc}'
               f'<span class="cat">{CAT_LABEL[e["cat"]]}</span></h3>')
    if e["say"]:
        out.append(f'<p class="say">Say: {entry_inline(e["say"])}</p>')
    for ln in e["rest"]:
        if ln.startswith("*See also:*"):
            names = [n.strip(" .") for n in
                     ln[len("*See also:*"):].split(",") if n.strip(" .")]
            links = []
            for name in names:
                slug = resolve_see_also(name, by_headword)
                esc = html.escape(name, quote=False)
                links.append(f'<a href="#{slug}">{esc}</a>' if slug else esc)
            out.append(f'<p class="ifield"><em>See also:</em> '
                       f'{", ".join(links)}.</p>')
        elif ln.startswith("**Refs:**"):
            out.append(f'<p class="irefs">{entry_inline(ln)}</p>')
        elif re.match(r"\*(Epithets|Also called|Kin):\*", ln):
            out.append(f'<p class="ifield">{entry_inline(ln)}</p>')
        else:
            out.append(f'<p class="ibody">{entry_inline(ln)}</p>')
    out.append("</article>")
    return "\n".join(out)


NAMES_JS = """\
<script>
(function () {
  var q = document.getElementById('q');
  var chips = document.querySelectorAll('.chip');
  var entries = document.querySelectorAll('.entry');
  var groups = document.querySelectorAll('.lgroup');
  var count = document.getElementById('count');
  var total = entries.length;
  var cat = '';
  function apply() {
    var needle = q.value.trim().toLowerCase();
    var shown = 0;
    entries.forEach(function (el) {
      var ok = (!cat || el.dataset.cat === cat) &&
               (!needle || el.dataset.key.indexOf(needle) !== -1);
      el.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('.entry:not([hidden])');
    });
    count.textContent = (shown === total) ? total + ' entries'
                                          : shown + ' of ' + total + ' entries';
  }
  q.addEventListener('input', apply);
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      cat = c.dataset.cat;
      chips.forEach(function (o) { o.classList.toggle('on', o === c); });
      apply();
    });
  });
})();
</script>"""


def build_names() -> str:
    entries = parse_index_entries()
    by_headword = {e["headword"]: e["slug"] for e in entries}
    unresolved = sum(
        1 for e in entries for ln in e["rest"] if ln.startswith("*See also:*")
        for n in ln[len("*See also:*"):].split(",")
        if n.strip(" .") and not resolve_see_also(n.strip(" ."), by_headword))
    if unresolved:
        print(f"  (names.html: {unresolved} see-also names left unlinked)")

    out = ['<nav class="booknav" data-pagefind-ignore>'
           '<a href="index.html">&lsaquo; Contents</a><span></span><span></span></nav>',
           '<header class="bookhead">',
           '<h1 data-pagefind-meta="title">Index of Names &amp; Places</h1>',
           '<p class="argument">every named person, god, people, and place in '
           'the poem — with pronunciations, epithets, kin, and linked '
           'citations</p>', '</header>']

    out.append('<div class="idxbar" data-pagefind-ignore>')
    out.append('<input id="q" type="search" placeholder="Filter by name…" '
               'autocomplete="off">')
    out.append('<div class="chips">')
    for val, label in CAT_CHIPS:
        on = " on" if val == "" else ""
        out.append(f'<button class="chip{on}" data-cat="{val}">{label}</button>')
    out.append(f'<span id="count">{len(entries)} entries</span>')
    out.append("</div>")
    letters = sorted({e["headword"][0].upper() for e in entries})
    out.append('<div class="letters">' + "".join(
        f'<a href="#{c}">{c}</a>' for c in letters) + "</div>")
    out.append("</div>")

    cur = ""
    for e in entries:
        letter = e["headword"][0].upper()
        if letter != cur:
            if cur:
                out.append("</section>")
            out.append(f'<section class="lgroup" id="{letter}">')
            out.append(f'<h2 class="letter" data-pagefind-ignore>{letter}</h2>')
            cur = letter
        out.append(render_entry(e, by_headword))
    out.append("</section>")
    out.append(NAMES_JS)

    return page("Index of Names & Places — the Odyssey, a Claudyssey",
                f"Every named person, god, people, and place in the Odyssey: "
                f"{len(entries)} entries with pronunciations, epithets, kin, "
                f"and line citations linked into the text.",
                "\n".join(out), indexed=True)


# ---------------------------------------------------------------------------
# Machine-readable mirror (docs/api/)


API_NOTE = (
    "Machine-readable mirror of the Claudyssey, a line-for-line English "
    "translation of Homer's Odyssey. book-NN.txt is the translation source "
    "for one book: numbered verse lines ('123  text', one English line per "
    "Greek line, same numbering as the Greek), [^L123] markers pointing into "
    "a '## Notes' section of scholarly endnotes, and an italic argument line. "
    "registry.json is the index of names: every named person, god, people, "
    "and place, with category, aliases, note, and 'book.line' refs. "
    "Cite passages as book.line, e.g. 9.366. Human-readable edition with "
    "line anchors: /read/book-NN.html#L123.")


def build_api() -> None:
    OUT_API.mkdir(parents=True, exist_ok=True)
    (OUT_API / "registry.json").write_text(
        REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")
    books = []
    for n in range(1, 25):
        src = SRC / f"book-{n:02d}.md"
        (OUT_API / f"book-{n:02d}.txt").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8")
        argument, stanzas, notes = parse_book(src)
        books.append({
            "book": n,
            "argument": argument,
            "last_line": stanzas[-1][-1][0],
            "notes": len(notes),
            "text": f"{SITE}/api/book-{n:02d}.txt",
            "html": f"{SITE}/read/book-{n:02d}.html",
        })
    manifest = {
        "title": "The Odyssey — a Claudyssey",
        "description": API_NOTE,
        "site": SITE,
        "repository": "https://github.com/spinchange/claudyssey",
        "license": ("Translation: CC0 1.0 (public domain dedication). "
                    "Notes and index: CC BY 4.0, (c) 2026 Chris Duffy. "
                    "Greek source (Murray 1919) public domain; Perseus "
                    "digitization CC BY-SA."),
        "registry": f"{SITE}/api/registry.json",
        "books": books,
    }
    (OUT_API / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (OUT_API / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API — the Odyssey, a Claudyssey</title>
<meta name="description" content="Plain-text and JSON mirror of the translation, for scripts and language models.">
<link rel="stylesheet" href="../read/read.css?v={css_version()}">
</head>
<body>
<div class="meander"></div>
<div class="wrap">
<p class="site"><a href="../">The Odyssey · a Claudyssey</a></p>
<header class="bookhead"><h1>Plain-text mirror</h1>
<p class="argument">the translation as data, for scripts and language models</p></header>
<p>{html.escape(API_NOTE)}</p>
<ul>
<li><a href="manifest.json">manifest.json</a> — all of the below, described</li>
<li><a href="registry.json">registry.json</a> — the name index with citations</li>
<li><code>book-01.txt</code> … <code>book-24.txt</code> — one file per book,
e.g. <a href="book-09.txt">book-09.txt</a></li>
</ul>
</div>
<div class="meander"></div>
<footer><a href="../read/index.html">Contents</a> · <a href="../">About &amp; downloads</a></footer>
</body>
</html>
""", encoding="utf-8")


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

.apparatus{margin:26px 0 8px; padding:12px 14px; font-size:.95rem;
  background:rgba(201,155,63,.07); border:1px solid rgba(201,155,63,.3);
  border-radius:6px}

footer{text-align:center; font-size:.8rem; opacity:.7; padding:20px 0 40px}

/* ---- site search (Pagefind default UI, re-themed) ---- */
#search{margin:6px 0 22px;
  --pagefind-ui-scale:.9;
  --pagefind-ui-primary:var(--gold);
  --pagefind-ui-text:var(--bone);
  --pagefind-ui-background:rgba(0,0,0,.25);
  --pagefind-ui-border:rgba(201,155,63,.45);
  --pagefind-ui-tag:rgba(201,155,63,.18);
  --pagefind-ui-border-width:1px;
  --pagefind-ui-border-radius:5px;
  --pagefind-ui-font:inherit}
#search .pagefind-ui__search-input{color:var(--bone)}
#search .pagefind-ui__search-input::placeholder{color:var(--bone); opacity:.55}
#search .pagefind-ui__result{border-color:rgba(201,155,63,.25)}
#search .pagefind-ui__result-link{color:var(--gold)}
#search .pagefind-ui__result-excerpt{color:var(--bone); opacity:.9}
#search mark{background:rgba(201,155,63,.4); color:inherit; border-radius:2px}
#search .pagefind-ui__button{background:rgba(201,155,63,.1); color:var(--gold);
  border:1px solid rgba(201,155,63,.45)}
#search .pagefind-ui__message{color:var(--bone); opacity:.8}

/* ---- index of names & places ---- */
.booknav .mid{min-width:0}
.idxbar{position:sticky; top:0; z-index:5; background:rgba(30,11,21,.96);
  margin:0 -22px 18px; padding:12px 22px 10px;
  border-bottom:1px solid rgba(201,155,63,.3)}
.idxbar input{width:100%; padding:9px 12px; font:inherit; color:var(--bone);
  background:rgba(0,0,0,.25); border:1px solid rgba(201,155,63,.45);
  border-radius:5px}
.idxbar input:focus{outline:none; border-color:var(--gold)}
.chips{display:flex; gap:7px; flex-wrap:wrap; align-items:baseline;
  margin-top:9px}
.chip{font:inherit; font-size:.8rem; color:var(--bone); cursor:pointer;
  background:rgba(0,0,0,.2); border:1px solid rgba(201,155,63,.35);
  border-radius:12px; padding:2px 11px}
.chip:hover{border-color:var(--gold)}
.chip.on{background:rgba(201,155,63,.25); color:var(--gold);
  border-color:var(--gold)}
#count{margin-left:auto; font-size:.8rem; opacity:.65; white-space:nowrap}
.letters{margin-top:9px; font-size:.85rem; letter-spacing:.1em}
.letters a{text-decoration:none; padding:0 2px}
.letters a:hover{text-decoration:underline}
.letter{font-weight:normal; color:var(--gold); font-size:1.5rem;
  letter-spacing:.1em; border-bottom:1px solid rgba(201,155,63,.3);
  margin:30px 0 14px; scroll-margin-top:120px}
.entry{margin:0 0 20px; scroll-margin-top:120px}
.entry:target{background:rgba(201,155,63,.1); border-radius:5px;
  padding:6px 10px; margin-left:-10px; margin-right:-10px}
.entry h3{font-weight:normal; font-size:1.12rem; margin:0 0 2px;
  color:var(--gold); display:flex; align-items:baseline; gap:.4em;
  flex-wrap:wrap}
.entry h3 .grc{opacity:.8; font-size:.95em; color:var(--bone)}
.entry h3 .cat{margin-left:auto; flex-shrink:0; white-space:nowrap;
  font-size:.68rem; letter-spacing:.1em;
  text-transform:uppercase; opacity:.55; color:var(--bone);
  border:1px solid rgba(234,217,180,.35); border-radius:10px;
  padding:1px 8px}
.say{margin:0 0 6px; font-size:.85rem; color:var(--gold); opacity:.85;
  font-variant:small-caps; letter-spacing:.04em}
.ibody{margin:0 0 6px; font-size:.95rem}
.ifield{margin:0 0 4px; font-size:.88rem; opacity:.88}
.irefs{margin:0 0 4px; font-size:.85rem; opacity:.85}
.cite{text-decoration:none; white-space:nowrap}
.cite:hover{text-decoration:underline}

@media (max-width:560px){
  .wrap{padding:0 14px}
  .verse{padding-left:2.1rem}
  .ln{left:-2.6rem; width:2rem}
  .toc b{min-width:4.6em}
  .idxbar{margin:0 -14px 16px; padding:10px 14px 8px}
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
    (OUT / "names.html").write_text(build_names(), encoding="utf-8")
    build_api()
    print("index.html + names.html + read.css + api/")
    print("now refresh the search bundle:  npx -y pagefind --site docs")


if __name__ == "__main__":
    main()
