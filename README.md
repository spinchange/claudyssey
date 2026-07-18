# The Odyssey — a line-for-line translation

A complete line-for-line English translation of Homer's Odyssey, an original
production by Claude Fable 5.

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

- `translation/book-01.md` … — one file per book, one English line per Greek
  line, keyed to the same line numbers.

## Licensing

Murray's 1919 Greek text is in the public domain. The Perseus digitization is
distributed under CC BY-SA; this repository retains that attribution for the
`greek/` directory. The English translation is original to this project.
