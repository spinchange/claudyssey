#!/usr/bin/env python3
"""Package the aligned corpus as a Hugging Face dataset, into hf-dataset/.

Emits:

    hf-dataset/README.md       the dataset card (YAML header + documentation)
    hf-dataset/odyssey.jsonl   all 12,107 aligned lines, one JSON object each
    hf-dataset/registry.json   the name index (CC BY 4.0), as an extra file

The output directory is generated and gitignored; rebuild it any time with

    python tools/build_hf_dataset.py

and upload with the huggingface CLI (or the web UI):

    hf auth login
    hf upload <user>/claudyssey-odyssey hf-dataset --repo-type dataset

The card's licensing section is the authoritative statement for the mixed
licensing (en: CC0, greek: CC BY-SA 4.0, registry: CC BY 4.0); keep it in
sync with the root LICENSE and the /api/ landing page if any of them change.
"""
from __future__ import annotations
import json

from build_web import GREEK, REGISTRY, ROOT, SITE, TOTAL_LINES, aligned_book

OUT = ROOT / "hf-dataset"

CARD = """\
---
license:
- cc0-1.0
- cc-by-sa-4.0
- cc-by-4.0
language:
- grc
- en
task_categories:
- translation
task_ids:
- machine-translation
pretty_name: "The Claudyssey: Homer's Odyssey, Greek-English aligned line by line"
size_categories:
- 10K<n<100K
tags:
- poetry
- homer
- odyssey
- ancient-greek
- parallel-corpus
- classics
- literature
configs:
- config_name: default
  data_files:
  - split: train
    path: odyssey.jsonl
---

# The Claudyssey: Homer's Odyssey, aligned Greek-English

A complete parallel corpus of Homer's Odyssey: all **12,107 verse lines**
of the Greek paired one-to-one with a line-for-line English translation,
keyed to the standard (Murray 1919) line numbering. The English translation
is dedicated to the public domain (CC0).

- **Website / reading edition:** https://theclaudyssey.com
- **Static API (this data, per book):** https://theclaudyssey.com/api/
- **Source repository:** https://github.com/spinchange/claudyssey

## What makes it useful

Public-domain English Odysseys exist (Butler, Palmer, Pope...), but none of
them align to the Greek line by line: they are prose, or verse with its own
lineation. Modern line-aware translations are under copyright. This corpus
is, as far as we know, the only complete English Odyssey that is both
line-aligned to the standard Greek numbering and free of copyright
restriction, which makes it usable for:

- **Alignment and translation research**: a 12,107-pair grc-en corpus of
  verse with exact line correspondence.
- **Evaluation**: any passage a model cites as `book.line` is checkable
  against any scholarly edition of the Greek.
- **Classics teaching and tooling**: reader interfaces, interlinears,
  vocabulary tools, without permissions overhead.

## Data

One JSON object per verse line, in the printed order of the Greek text:

```json
{"book": 9, "line": 366, "greek": "Οὖτις ἐμοί γʼ ὄνομα· Οὖτιν δέ με κικλήσκουσι", "en": "Nobody is my name. Nobody is what they call me —"}
```

| field | type | description |
|---|---|---|
| `book` | int | 1-24 |
| `line` | int | Murray's line number (the standard vulgate numbering) |
| `greek` | str | the Greek line (Murray 1919, via Perseus) |
| `en` | str | the English line, verse only (no note markers) |

Edition quirks, faithful to Murray 1919 and mirrored exactly in both
languages: two pairs print in transposed order (3.304-305, 14.63-64; rows
keep the printed order, so `line` is briefly non-monotonic there), and three
lines are omitted as later interpolations (10.456, 16.101, 23.49; the
numbering skips them). Hence 12,107 lines rather than 12,110.

`registry.json` (an extra file, not a split) is the poem's name index: 434
entries covering every named person, god, people, and place, with category,
aliases, a one-line gloss, and every `book.line` citation.

## Provenance, stated plainly

The English was produced by a large language model (Claude, Fable 5)
translating from the Greek line by line under a fixed set of constraints,
and edited by a human (Chris Duffy). Every line was verified one-to-one
against the Greek; the poem's repeated formulas are rendered identically at
each recurrence (a published register records every fixed choice); the full
revision history is public in the repository.

Because an AI translation invites the suspicion that it recombines prior
translations, that question was measured rather than asserted: n-gram
overlap and shared-passage analysis against nine translations from Pope to
Green, with all human-vs-human pairs as controls and the method and code
published. Results, including what the tests can and cannot rule out:
https://theclaudyssey.com/independence.html

The Greek is A. T. Murray's 1919 Loeb text as digitized by the Perseus
Digital Library (CTS URN `urn:cts:greekLit:tlg0012.tlg002.perseus-grc2`,
from [PerseusDL/canonical-greekLit](https://github.com/PerseusDL/canonical-greekLit)).

## Licensing

Three layers, separated by field:

| content | license |
|---|---|
| `en` fields (the English translation) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) - public domain dedication |
| `greek` fields | Murray 1919 is public domain; the Perseus digitization is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (attribute Perseus if you redistribute the Greek) |
| `registry.json` (the name index) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), (c) 2026 Chris Duffy |

The English on its own may be used for anything, including commercially,
with no permission or credit required.

## Citation

If you use this corpus, cite the edition:

```
Homer. The Odyssey. Translated by Claude (Fable 5), edited and produced by
Chris Duffy. 2026. https://theclaudyssey.com (translation CC0 1.0).
Greek text: A. T. Murray (1919), via the Perseus Digital Library.
```
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    with (OUT / "odyssey.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for n in range(1, 25):
            rows = aligned_book(n)
            total += len(rows)
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if total != TOTAL_LINES:
        raise SystemExit(f"{total} lines, expected {TOTAL_LINES}")
    (OUT / "registry.json").write_text(
        REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")
    (OUT / "README.md").write_text(CARD, encoding="utf-8")
    print(f"hf-dataset/: odyssey.jsonl ({total} lines), registry.json, "
          f"README.md")
    print("upload:  hf upload <user>/claudyssey-odyssey hf-dataset "
          "--repo-type dataset")


if __name__ == "__main__":
    main()
