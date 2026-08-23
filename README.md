# The Odyssey — a line-for-line translation

A complete line-for-line English translation of Homer's Odyssey.

- **From the Greek of** Homer
- **Translated by** Claude (Fable 5)
- **Edited and produced by** Chris Duffy

The EPUB records these as EPUB3 creators with MARC relator roles (`aut`, `trl`,
`edt`) and states them on the title page. The library-listing author is kept as
"Homer" by convention.

## Source text

The Greek is A. T. Murray's text from the Loeb Classical Library edition
(*Homer: The Odyssey*, 2 vols., Heinemann/Putnam, 1919), as digitized by the
Perseus Digital Library (CTS URN `urn:cts:greekLit:tlg0012.tlg002.perseus-grc2`,
from the [PerseusDL/canonical-greekLit](https://github.com/PerseusDL/canonical-greekLit)
repository). Full polytonic ancient Greek with standard vulgate line numbering.

- `greek/tlg0012.tlg002.perseus-grc2.xml` — the TEI XML as downloaded
- `greek/book-01.txt` … `book-24.txt` — extracted plain text, one line per
  verse, tab-separated as `<line number>\t<Greek>`
- `tools/extract_books.py` — the extraction script (rerun it to regenerate the
  per-book files from the XML)

12,107 lines total. Known edition quirks, faithful to Murray:

- **Transposed lines:** 3.304–305 and 14.63–64 are printed in swapped order
  (traditional numbering retained).
- **Omitted lines:** 10.456, 16.101, and 23.49 are absent (athetized as
  interpolations); numbering skips them.

## Translation

**Complete: all 24 books, 12,107 lines — every line verified one-to-one
against the Greek.**

- `translation/book-01.md` … `book-24.md` — one file per book, one English
  line per Greek line, keyed to the same line numbers. Each book carries a
  scholarly annotation apparatus (1,260 notes across the poem) as markdown
  footnotes keyed to line numbers.
- `FORMULAS.md` — the authoritative register of fixed renderings: Homer's
  repeated epithets, speech-formulas, and whole-line refrains recur verbatim
  in the English wherever the Greek repeats, and this file records every
  fixed choice and cross-book echo.

The voice is a loose five-to-six-beat unrhymed line. Names use familiar
Latinate spellings. δμώς/δμῳή are rendered "slave/slave-woman" throughout;
untranslatable puns are shadowed rather than dropped (the name-pun ὀδυσσάμενος
appears as "Odysseus, Man at Odds").

## Audiobook pipeline

`audiobook-source/` is a copied working set for generated audio. The original
`translation/` files should remain untouched.

`tools/build_audiobook.py` builds a single-narrator OpenAI TTS audiobook in
stages:

```powershell
python tools\build_audiobook.py prepare
```

This writes cleaned narration text to `audiobook-build/clean/`, TTS-sized
chunks to `audiobook-build/chunks/`, and a manifest to
`audiobook-build/manifest.json`. Cleanup removes verse line numbers, inline
footnote references, and the `## Notes` apparatus.

After setting `OPENAI_API_KEY`, generate audio chunks:

```powershell
$env:OPENAI_API_KEY = "..."
python tools\build_audiobook.py synthesize --voice fable --model gpt-4o-mini-tts
```

To test one book first:

```powershell
python tools\build_audiobook.py synthesize --books book-01
```

If `ffmpeg` is installed, join chunks into per-book audio files:

```powershell
python tools\build_audiobook.py concat --full
```

The final outputs are written under `audiobook-build/audio-chunks/` and
`audiobook-build/books/`. Existing generated chunks are skipped unless
`--force` is passed, so interrupted runs can be resumed.

## EPUB pipeline

`tools/build_epub.py` builds a high-quality EPUB3 with working bidirectional
footnote links (tap a note marker to jump to the note; tap the ↩ to return to
your place in the verse). It leaves `translation/` untouched.

```powershell
python tools\build_epub.py --books 1     # Book 1 only (proof of concept)
python tools\build_epub.py               # all 24 books
```

What the build does:

- **Footnote namespacing.** Every book reuses `[^L1]`, `[^L10]`, …; the script
  rewrites each book's ids to be book-unique (`[^b01-L1]`) so labels don't
  collide when Pandoc concatenates all 24 books, then Pandoc generates the
  forward links. `epub-build/backlinks.lua` injects the ↩ return link into each
  note so navigation is bidirectional even on readers without epub3 popup
  footnotes (Apple Books/Kobo also get tap-to-reveal popups for free).
- **Line-for-line layout.** Each verse keeps its own line (Pandoc hard breaks)
  with the line number hung in the margin. Every verse also carries an anchor
  (`#v{book}-{line}`) so it can be linked to.
- **Linked index.** `index/index.md` (names, pronunciations, epithets, kin,
  citations) is appended as back matter, and every `book.line` citation is
  turned into a live link to that verse's anchor (ranges and `ff` link to their
  first line). ~1,470 citation links across 434 entries.
- **Theming.** `epub-build/style.css` uses the cover's Geometric-vase palette
  (wine `#46192b`, bone, gold `#c99b3f`), with the cover art
  (`art/claudyssey-cover.svg`) rasterized to `epub-build/assets/cover.jpg`.
- **Greek.** Polytonic Greek is set in Gentium Plus (SIL OFL), subsetted to the
  used ranges as woff2 (~190 KB) and embedded, so the Greek in the notes renders
  on every device.

The Kindle and PDF editions are calibre conversions of the EPUB (the PDF's
page-count target is A5 at 17pt, matching the print-style layout):

```powershell
ebook-convert epub-build\odyssey.epub epub-build\odyssey.azw3
ebook-convert epub-build\odyssey.epub epub-build\odyssey.pdf --paper-size a5 --pdf-default-font-size 17
```

`tools/check_epub.py <file.epub>` is a lightweight structural validator
(mimetype, OPF manifest/spine, and every internal link — including the
noteref↔backlink pairing). It is not a substitute for W3C `epubcheck`, but
catches the build regressions that break readers.

Requires Pandoc (`winget install JohnMacFarlane.Pandoc`) and, for regenerating
the subsetted font, `fonttools` + `brotli`.

## Print edition

`tools/build_print.py` builds a press-ready PDF interior for print-on-demand
(KDP, IngramSpark, Lulu). It is a separate build from the EPUB, not a
conversion of it, because paper needs different decisions: a fixed measure,
line numbers every fifth line instead of every line, printed note numerals
instead of tappable links, running heads, folios, and book openers on a
recto. It leaves `translation/` untouched.

```powershell
python tools\build_print.py                  # all 24 books, 6x9in
python tools\build_print.py --books 1        # Book 1 only (proof)
python tools\build_print.py --trim 5.5x8.5   # digest
python tools\build_print.py --trim a5        # ISO A5
```

The default is **6x9in US trade**, black ink. What the build does:

- **Measure set by the verse.** This is a line-for-line translation, so a
  verse that wraps stops looking like one line. The poem's verses run to 90
  characters (median 53); at 10.5pt the measure holds about 71 characters
  and roughly 2% turn over, and those that do are indented so they still
  read as continuations rather than as new verses.
- **A contents page**, listing each book with its argument — the one-line
  summary that also stands under the book's title — and its printed folio,
  followed by the index. Printed page numbers only exist after pagination,
  so the contents is built empty, the folios are measured, and the book is
  rendered again with them filled in. The empty and filled pages are the
  same size (same rows, same leading; only the numerals differ), so nothing
  moves between the two passes and the numbers stay true. The builder
  re-measures afterwards and warns if anything shifted anyway.
- **Line numbers every fifth line**, hung in the margin. Numbering all
  12,107 is right for a linked digital text and noise on a page.
- **Endnotes per book**, numbered through each book, each note also giving
  the verse line it belongs to (*l. 337*) — which is how it should be cited.
- **Recto-forcing.** Book openers belong on a right-hand page. The builder
  renders, measures where each book landed, inserts a blank leaf before the
  first book that opened on a verso, and repeats. It fixes one book per pass
  and never takes a blank back, which is what makes it terminate — inserting
  a blank changes the length of everything after it, so reconsidering every
  book each pass just oscillates.
- **Furniture set for facing pages.** The running head is centered; the
  folio sits on the outside edge of each page (bottom-left on a verso,
  bottom-right on a recto), so the numbers stay visible while flipping.
- **Front matter and blank leaves carry no folio.** Page 1 is the poem's
  first page, and the title page, copyright, epigraph, note, and every
  inserted blank print neither a running head nor a page number.
- **Print-safe geometry.** Nothing, including the running head and folio,
  sits within the ±3mm a printer cuts to.

### Cover artwork as PDF

`tools/build_cover_pdf.py` renders an SVG in `art/` to a borderless
single-page PDF, sized to the artwork's own aspect ratio with the design
running edge to edge:

```powershell
python tools\build_cover_pdf.py                   # art/claudyssey-cover.pdf, 8x12in
python tools\build_cover_pdf.py --width 6         # a 6in-wide page
python tools\build_cover_pdf.py --bleed 0.125     # add print bleed on all sides
python tools\build_cover_pdf.py --svg art\claudyssey-social.svg
```

The output is vector — real paths and embedded Palatino text, so it scales
and prints at any size. The single raster in the file is the `feTurbulence`
grain layer, which has no PDF equivalent and is rasterized at ~300ppi; that
is the intended result, since the grain is part of the design.

Two things are load-bearing and easy to break. The SVG is referenced with an
`<img>` tag rather than inlined: calibre's html→epub step rewrites inline
SVG and discards `<defs>`, which silently strips the gradients, the
meander/zigzag/dot patterns, and the grain, leaving a bare bone-coloured
field. And every margin — both `--margin-*` and `--pdf-page-margin-*` — has
to be zero, or a white border appears around the art. The script verifies the
result by rendering the page and sampling its outermost pixels, because a
white edge is invisible in the page-size numbers.

### Paperback case wrap

`tools/build_wrap.py` builds the printed case — back cover, spine, and front
cover as one flat landscape page, to a print supplier's spec:

```powershell
python tools\build_wrap.py                  # art/claudyssey-wrap.pdf
python tools\build_wrap.py --pages 604      # a different page count
python tools\build_wrap.py --spine 1.42     # Lulu's figure, if it differs
python tools\build_wrap.py --no-url         # omit the site URL
python tools\check_wrap.py art\claudyssey-wrap.pdf
```

The geometry follows the interior's page count (595 pages in
`print-build/odyssey-print-6x9.pdf`, front matter and recto blanks
included): two fixed 6.125 in panels — a 6×9 trim with 0.125 in bleed on
every outside edge — either side of a spine set by Lulu's published
paperback formula, pages ÷ 444 + 0.06 in, the same for every stock they
offer: 595 ÷ 444 + 0.06 = 1.400 in, for 13.650 × 9.25 in overall. Only
the spine moves with the page count; the panels never do. The formula is
pinned by the spec Lulu issued for the earlier 590-page interior, which it
reproduces exactly (590 ÷ 444 + 0.06 = 1.3888 → 1.389 in, 13.639 in
wide). The Requirements panel at Lulu's cover-upload step shows their
figure for the page count actually uploaded; `--spine` takes it if it
ever differs.

The artwork is generated into `art/claudyssey-wrap.svg` and rendered from
there, so the wrap is reproducible rather than hand-placed. The back cover
sets its blurb by fitting: the type steps down until the text block fits the
space between the epigraph and the wave band, because wrapping text by
character count overruns the frame on wide words like "book.line".

Three notes specific to this output. The front panel drops the `feTurbulence`
grain used on the standalone cover — it is the one element with no vector
equivalent, and keeping it would force a raster into a file the supplier
requires flattened. The decorative bands (meander, dots, zigzag) are drawn
as SVG `<pattern>` fills, which calibre's renderer would paint into
page-sized 72 ppi bitmaps — Lulu's preflight flags those as under 200 ppi —
so the builder expands each pattern into explicit clipped `<use>` tiles
before rendering; same picture, vector encoding. And calibre cannot express
the required page width:
`--custom-size` quantizes to a 1.2 pt grid, so 13.639 in (982.008 pt) came
out as 982.080 and the next step down is 980.880 (13.650 in is 982.8 pt, on
the grid by luck; the next page count will not be). The artwork is laid out
to the exact figure regardless, so the builder cuts the page boxes to it
afterwards and leaves the drawing alone.

`tools/check_wrap.py` checks the file against each of the supplier's
requirements — one page, exact dimensions, fonts embedded, flattened (no
optional content groups, annotations, or form fields), no raster below
300 ppi anywhere, including inside pattern and soft-mask resources — plus
the two things
the spec implies but does not state: that the art bleeds to all four edges,
and that no light-coloured content sits inside the bleed where trimming
would cut it. That last check is the one that matters; it catches overrunning
text, which no amount of measuring the page size will reveal.

`tools/check_print.py` validates the finished PDF against the specification
— trim size, verse point size, margins on every page, nothing overset past
the trim, all fonts embedded, the turnover rate, and that every page number
on the contents page really does point at the section it names:

```powershell
python tools\check_print.py print-build\odyssey-print-6x9.pdf
```

Run it after any rebuild. The PDF stage depends on several undocumented
behaviours of calibre's renderer: content margins render at 2× their stated
value; `--pdf-default-font-size` is scaled by 0.75, so only sizes that are a
multiple of 0.75pt are reachable (hence a 10.5pt body); `@page` rules and
`:left`/`:right` mirroring are dropped entirely; and class-based CSS is
rewritten during the EPUB step, so anything load-bearing has to be an inline
style. Those were established by measuring output, and a calibre upgrade can
change them silently — the PDF still builds, it is just wrong. The checker is
what catches that.

Two of those were only visible in a full build, which is worth knowing before
trusting a single-book proof: calibre also rescales fonts by a factor that
depends on document length (a one-book proof suggested 0.844 where the real
figure is 0.75), and three characters in the notes — `ʼ`, `→`, `≈` — are
absent from the subsetted Gentium and fall back to Arial mid-Greek. The
builder maps them to glyphs the font has (the koronis `᾽`, an en dash, and
`c.`), and the checker fails if any new character starts falling back.

Because mirrored margins cannot be expressed, the inner and outer margins
are both generous enough to serve as a gutter. `--odd-even-offset N` adds
calibre's CropBox-based shift for a deeper gutter, but many print shops
ignore the CropBox, so it is opt-in rather than relied on.

Requires calibre (`ebook-convert`), plus `pdfplumber` and `pypdf` for the
recto pass and the checker.

## Web edition

`tools/build_web.py` regenerates the reading edition in `docs/read/` (served by
GitHub Pages): one page per book with line anchors and endnotes, a contents
page with site search, and `names.html` — the index of names & places rendered
from `index/index.md`, with category/letter/text filtering and every `book.line`
citation deep-linked into the text (`book-12.html#L184`).

Site search is [Pagefind](https://pagefind.app), fully static (the bundle lives
in `docs/pagefind/`). It indexes exactly the poem, the notes, and the name
index (`pagefind.yml` disables stemming so name searches stay exact).

The build also emits `docs/api/` — a machine-readable mirror for scripts and
language models, served at `theclaudyssey.com/api/` with its own landing
page: `manifest.json`, `registry.json` (the name index with refs),
`book-NN.txt` (each book's translation source, verbatim), and
`aligned-NN.jsonl` — the Greek↔English parallel corpus, one JSON object per
verse line (`{book, line, greek, en}`), keyed to Murray's numbering with his
transpositions and omissions preserved. The build fails if the aligned
corpus doesn't come out to exactly 12,107 lines.

`tools/build_hf_dataset.py` packages the same corpus as a Hugging Face
dataset (`hf-dataset/`, gitignored): `odyssey.jsonl` (all 24 books),
`registry.json`, and a dataset card with the per-field licensing.

Every generated page carries canonical, Open Graph, and Twitter-card
metadata with absolute URLs, pointing at `docs/social.jpg` — the 1200x630
link-preview card rendered from `art/claudyssey-social.svg` by
`tools/build_social_image.py` (via the calibre cover pipeline, then
rasterized with PyMuPDF; rerun it only when the social artwork changes).
The build also writes `docs/sitemap.xml`, referenced from `robots.txt`.

In the reading edition, every verse line's gutter number is a copyable
permalink: the every-fifth-line numbers are always visible, the rest appear
on hover (and stay out of the way on touch screens), and clicking one puts
the absolute `#L`-anchored URL on the clipboard as well as navigating to it.

After any rebuild:

```powershell
python tools\build_web.py
npx -y pagefind --site docs
```

## Licensing

**The English translation** (the 12,107 lines in `translation/book-*.md`,
verse text only) is dedicated to the public domain under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Copy it,
print it, teach it, set it to music, remix it; no permission or credit is
required, for any purpose including commercial use.

**The apparatus** — the line notes (the footnote blocks in those same
files), the introduction and front matter, the index of names and places
(`index/`), the register of fixed renderings (`FORMULAS.md`), and the
independence analysis (`docs/independence.html`) — is
(c) 2026 Chris Duffy, licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use it freely
with attribution.

**The Greek**: Murray's 1919 text is in the public domain. The Perseus
digitization is distributed under CC BY-SA; this repository retains that
attribution for the `greek/` directory.

The EPUB embeds Gentium Plus under the SIL Open Font License; the license text
travels with the font in `epub-build/assets/GentiumPlus-OFL.txt`.
