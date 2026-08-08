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

`tools/check_epub.py <file.epub>` is a lightweight structural validator
(mimetype, OPF manifest/spine, and every internal link — including the
noteref↔backlink pairing). It is not a substitute for W3C `epubcheck`, but
catches the build regressions that break readers.

Requires Pandoc (`winget install JohnMacFarlane.Pandoc`) and, for regenerating
the subsetted font, `fonttools` + `brotli`.

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
language models: `manifest.json`, `registry.json` (the name index with refs),
and `book-NN.txt` (each book's translation source, verbatim), served at
`theclaudyssey.com/api/`.

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
(`index/`), and the independence analysis (`docs/independence.html`) — is
(c) 2026 Chris Duffy, licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use it freely
with attribution.

**The Greek**: Murray's 1919 text is in the public domain. The Perseus
digitization is distributed under CC BY-SA; this repository retains that
attribution for the `greek/` directory.

The EPUB embeds Gentium Plus under the SIL Open Font License; the license text
travels with the font in `epub-build/assets/GentiumPlus-OFL.txt`.
