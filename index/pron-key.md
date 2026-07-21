# Pronunciation key — house style

The index gives each non-obvious name a pronunciation in the `*Say:*` field.
This is the house style those respellings follow.

## Convention

**Traditional anglicized pronunciation** — the established English/Latinate
reading — *not* reconstructed ancient Greek. This is the only choice consistent
with the translation's Latinate spellings: you cannot print "Circe" and say
"KIR-ke." Where the anglicized tradition is itself split (and for these names it
often is), the field gives one respelling and notes the variant with "*or*".

## Notation

Plain respelling; syllables hyphenated; **primary stress in CAPS**; unstressed
vowels reduced to the schwa `uh`.

### Vowel key (anchor words)

| respell | as in | respell | as in |
|---|---|---|---|
| `a` | c**a**t | `oh` | g**o** |
| `ah` | f**a**ther | `aw` | s**aw** |
| `ay` | d**ay** | `oo` | f**oo**d |
| `air` | c**are** | `yoo` | (eu-) f**ew** |
| `e` | b**e**d | `u` | c**u**p |
| `ee` | s**ee** | `ur` | f**ur** |
| `i` | s**i**t | `uh` | schwa, **a**bout |
| `eye` / `y` | sk**y** | `ow` | n**ow** |

**Consonants:** `g` is hard ("get") unless written `j`; `th` is voiceless
("thin"); Greek χ and Latin `ch` become `k`; `s`, `k`, `z` are always written as
the sound, never the letter.

## The two rules

1. **Sound shifts.** `c` before e/i/y/ae → `s` (Circe → SUR-see); `g` before
   e/i/y → often `j` (Aegisthus → ee-JIS-); `ae`/`oe` → `ee`; `eu` → `yoo`;
   `ei` → `eye`; `ou`/`ou` → `oo`; final `-es` → `-eez`; `Ps-`/`Cn-`/`Ct-` drop
   the first letter; `ch`/`chi` → `k`.
2. **Stress (the Latin Penult Rule).** Stress the **penult** if it is heavy (long
   vowel, diphthong, or vowel + two consonants); otherwise the **antepenult**.
   Penult weight follows the **Greek vowel quantity**, which `tools/scan.py`
   already computes — so stress placement is checkable against the Greek, not
   guessed.

## Data & regeneration

- The respellings live in **`index/pronunciations.tsv`** — one row per headword
  (`headword` ⇥ `say` ⇥ optional `variant`). It is meant to be scanned and
  corrected by hand; it is the single source of truth.
- `tools/merge_index.py` reads it and injects the `*Say:*` field into each entry
  when it builds `index/index.md`. Editing a pronunciation means editing one row
  and re-running the merge.
- Transparent English names (Troy, Crete, Sparta, Athens, Egypt, and the like)
  and the descriptive/collective headwords (Dawn, the Winds, the Muses) carry no
  row and get no `*Say:*` field.
