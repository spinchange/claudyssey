# Audio regeneration batch — errata patches of 2026-08-21

Two text-patch passes changed 54 verse lines (reading + performance files):

1. **Books 13–24 pass** — 7 verified mistranslations fixed (13.15, 14.533,
   17.455, 17.494, 23.67–68, 23.166, 23.196, 23.324, 24.294) plus name-spelling
   normalization to the Books 1–12 house style (Eumaeus, Menelaus, Athena,
   Cronos, Telemachus, Eurycleia, Penelope).
2. **Books 1–12 errata pass** — 24 verified errors fixed across 27 lines
   (worst: 1.300 Aegisthus-as-patricide, 8.229 dropped negative, 2.133
   "send my mother against him", 7.344 chamber-for-portico, 11.609 invented
   breastplate, 9.372–373 duplicated clause). Book 5 was clean and is untouched.

## What is stale

`prepare` was re-run against the patched text (same `--max-chars 3800`, no
audio touched) and every chunk was hash-compared with the pre-patch snapshot.
**42 of 254 chunks changed**, recorded in
`audio-openai-fable/stale-chunks.json`:

| Book | Stale chunks |
|---|---|
| 01 | 7, 8, 10 |
| 02 | 3 |
| 03 | 2 |
| 04 | 3, 4, 5, 6, 12 |
| 06 | 7 |
| 07 | 3, 4, 6, 8 |
| 08 | 2, 5, 7 |
| 09 | 2, 8 |
| 10 | 7, 9, 12 |
| 11 | 6, 13, 15 |
| 12 | 5 |
| 13 | 2 |
| 14 | 2, 9, 10, 11 |
| 16 | 10 |
| 17 | 9, 10 |
| 18 | 8 |
| 23 | 2, 3, 4, 5, 7 |
| 24 | 7 |

Books 05, 15, 19, 20, 21, 22 need no new synthesis. All four listening
volumes must be re-concatenated (each contains at least one changed book).

## To run (needs OPENAI_API_KEY and ffmpeg)

```
cd hexameter-retranslation/audio-openai-fable
python regen-stale.py --dry-run   # inspect the plan
python regen-stale.py             # ~143k characters of gpt-4o-mini-tts
```

The runner deletes exactly the 42 stale chunk mp3s, re-synthesizes them with
each book's recorded production settings (fable voice, 0.96 speed, the epic
instructions, per-book pronunciation-fixes file where one exists),
re-concatenates the 18 affected book files, rebuilds the four volume mp3s in
`books/`, and refreshes the top-level volume copies.

Caveats:

- Books 09–24 have no per-book production-settings file; the runner falls back
  to `production-settings.json` (same voice/model/speed/instructions,
  `pronunciation-fixes.tsv`). If those books were originally synthesized with
  different pronunciation flags, spot-check one regenerated chunk first.
- `audio-elevenlabs-ge-america/` is a Book 1 audition (text prep only, no
  audio). Its chunks predate the patches — re-run `prepare` for that build dir
  before any future ElevenLabs synthesis.
