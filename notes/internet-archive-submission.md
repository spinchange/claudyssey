# Internet Archive submission

Draft metadata for uploading the ebook edition to archive.org. Text only —
the audiobook is held back until its rights layer is settled (see LICENSE §
"Audio").

## Item 1 — the ebook edition (ready)

Upload at https://archive.org/upload/

### Files to upload

    epub-build/odyssey.epub     1.27 MB   primary
    epub-build/odyssey.azw3     1.91 MB
    epub-build/odyssey.pdf      5.76 MB

Upload the EPUB **first**. IA derives its own formats from the first text
file it sees, and an EPUB source produces better derivatives (full-text
search, online reader) than a PDF source. The AZW3 and PDF ride along as
additional formats.

### Metadata fields

| Field | Value |
|---|---|
| `title` | The Odyssey: A Line-for-Line English Translation |
| `creator` | Homer |
| `subject` | Homer; Odyssey; Greek literature; epic poetry; classics; translation; machine translation; CC0 |
| `date` | 2026 |
| `language` | English (with parallel Ancient Greek source) |
| `licenseurl` | https://creativecommons.org/publicdomain/zero/1.0/ |
| `mediatype` | texts |
| `collection` | opensource (Community Texts) |

### Description

> A complete line-for-line English translation of Homer's *Odyssey* — all 24
> books, 12,107 lines, with one English line for every line of the Greek and
> the same line numbering throughout, so any passage can be cited as
> book.line and found in either language.
>
> **Translated by Claude (Fable 5), a large language model, under the
> editorial direction of Chris Duffy.** The translation is dedicated to the
> public domain under CC0 1.0: no permission or attribution is required for
> any use, commercial or otherwise.
>
> The edition includes a scholarly apparatus of 1,260 line notes, an index of
> every named person, god, people, and place with citations, and a register
> of fixed renderings recording how Homer's repeated epithets, speech
> formulas, and whole-line refrains recur verbatim in the English wherever
> they recur in the Greek. The apparatus is © 2026 Chris Duffy under CC BY
> 4.0.
>
> The Greek source is A. T. Murray's text from the Loeb Classical Library
> edition (Heinemann/Putnam, 1919), public domain, as digitized by the
> Perseus Digital Library and used under CC BY-SA. Murray's edition quirks
> are preserved: lines 3.304–305 and 14.63–64 stand in their transposed
> order, and lines 10.456, 16.101, and 23.49 are absent as athetized
> interpolations, with the traditional numbering retained across the gaps.
>
> Web edition, machine-readable API, and full source:
> https://theclaudyssey.com

### Notes on the field choices

**`creator: Homer`** follows library convention — the author of the work,
not of the translation. IA's metadata has no MARC relator support, so the
translator credit cannot be encoded structurally the way the EPUB does
(`aut` / `trl` / `edt`). It therefore has to live in the description, which
is why the machine-translation disclosure sits in the second paragraph in
bold rather than buried at the end. Anyone reading the record at a glance
sees it.

**`licenseurl`** takes a single URL and the item holds two licenses. CC0 is
the correct one to declare: it governs the translation, which is the bulk of
the work and the thing people will reuse. The CC BY apparatus is stated in
the description and in the EPUB's own Dublin Core `dc:rights`, so the
distinction survives even if the file is copied off IA without its record.

**`collection: opensource`** is the self-upload collection for
community-contributed texts. Do not request `americana` or a library
collection — those are for scanned institutional holdings and a curator will
reject the item.

## Item 2 — the audiobook (blocked)

Do not upload until resolved:

1. Whether OpenAI's terms permit redistributing generated speech as a
   standalone published work released into a public archive.
2. What license to declare on the narration, given the underlying text is
   CC0 but the generated audio is a separate layer that may not be ours to
   dedicate.

Keep this as a **separate IA item** rather than adding audio files to the
ebook item. Different `mediatype` (`audio` vs `texts`), different license,
different audience, and IA's derivation pipeline treats mixed-media items
poorly.

## Post-upload

- Add the IA identifier/URL to README.md and to `docs/api/manifest.json`.
- The IA item URL is a durable citation target; consider linking it from the
  site footer alongside the GitHub repository.
