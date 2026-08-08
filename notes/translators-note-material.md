# Material for the Translator's Note / Introduction

A running catalog of observations, discussions, and principles worth drawing on
when the introduction or translator's note is eventually written. Add to this
file as new material comes up; nothing here is final prose.

## 1. The line-for-line constraint is about timing, not arithmetic

The one-to-one line correspondence (12,107 lines, same numbering, same gaps at
10.456, 16.101, 23.49) is not a formal stunt. Keeping Homer's word order means
keeping his *timing*: which word ends a line, which word opens the next, what
collides across the break. Homer does substantial poetic work with placement,
and a translation that reorders freely silently discards it.

Honest caveat to state somewhere: "line-for-line" means the numbering
corresponds one-to-one, not that every English line is fully self-contained —
Greek enjambment sometimes forces a phrase to shift slightly between adjacent
lines.

## 2. Case study: 1.13–15, the wife/nymph garden path

> 13 Him alone, aching for homecoming and his wife,
> 14 the queenly nymph Calypso, shining among goddesses, held back
> 15 in her hollow caves, hungry to make him her husband.

Read aloud, the English momentarily lets Calypso *be* the wife — the
appositive reading holds until "held back" arrives and forces a re-parse.

What's happening:

- The Greek really does end line 13 with γυναικός ("wife") and open line 14
  with νύμφη πότνια ("the queenly nymph"), verb ἔρυκε buried mid-line. The
  translation preserves that order.
- A Greek listener never garden-paths: γυναικός is genitive (object of
  "aching for"), νύμφη nominative (subject of "held back"). Case endings
  announce "new character, new clause" instantly. English has no case
  marking, so word order alone carries the grammar — the flicker of ambiguity
  is the cost of preserving Homer's placement in an uninflected language.
- But the juxtaposition is arguably deliberate in Homer: "wife" and "nymph"
  flush against each other across the line break — and νύμφη can also mean
  "bride." Line 15 closes the loop: Calypso is λιλαιομένη πόσιν εἶναι,
  longing to be his wife. The wife he aches for is answered immediately by
  the would-be wife who aches for him. In Greek it is a pointed ironic
  collision; in English the collision sharpens into a momentary genuine
  ambiguity — the same effect, slightly louder.
- Verdict (discussed with the reader, 2026-07-20, revised same day): keep the
  word order untouched, but wall off the parenthetical with em dashes — "Him
  alone — aching for homecoming and his wife — / the queenly nymph Calypso…"
  Punctuation does silently what Greek case endings did audibly: it marks
  "new clause coming" without moving a single word. The ironic wife/nymph
  juxtaposition across the line break survives intact; only the false
  appositive parse is blocked. The reader's argument for the change: a
  first-time reader will be less confused — "I was, and I know the story
  cold." Punctuation is the translation's substitute inflection; this is a
  principle worth stating in the note.

This is a good flagship example for the note: it shows the constraint
*earning* something a free translation would lose.

## 2b. Counter-case: 2.60/62, the collision you kill

The original rendering of Telemachus' assembly speech read "We are not the men
to beat it off" (2.60) and "Beat it off I would, if only the strength were in
me!" (2.62) — accidental contemporary slang, catastrophic read aloud, and
worse for being spoken by a young man lamenting his own inadequacy. Caught by
a reader on a read-aloud pass (2026-07-20); revised to "beat it back."

Why it happened, and why the fix was cheap:

- The Greek hammers ἀμύνω three times in four lines (59 ἀμῦναι, 60 ἀμυνέμεν,
  62 ἀμυναίμην) — Odysseus could ward ruin off; we cannot; I would if I had
  the strength. The translation rightly kept the repetition with "beat," but
  pronominalizing "ruin" produced "beat it off."
- "Beat it back" preserves the identical verb across all three lines (59
  "beat ruin away from the house" stands unchanged), the martial register,
  and the beat count.
- Not a locked formula: ἀμύνω's other occurrences (12.114, 21.195, 22.214)
  are each rendered differently, so only two lines were touched.

Pairs with §2 as the two sides of one principle for the introduction: the
wife/nymph flicker resolves *with* the poem, so it stays; "beat it off"
resolves *against* it, into comedy, so it goes. The test is not "is there a
momentary mis-hearing?" but "which way does the mis-hearing point?"

## 3. Kept collisions — the same philosophy elsewhere

The translation deliberately preserves collisions rather than smoothing them:

- **Epithets vs. moral bookkeeping:** "blameless Aegisthus" (1.29) — an
  adulterer-murderer with an honorific epithet, because in oral verse
  epithets belong to names and meter, not morality. Kept, with a note.
- **Line-end suspension:** the recognition scenes of Books 19 and 23 use
  line-end suspension almost cruelly; worth mining for further examples when
  writing the note.
- See also FORMULAS.md's principle: repeated formulas recur verbatim in
  English wherever the Greek repeats.

## 4. Other settled points worth restating in the note

(Recorded in README/FORMULAS but belonging in the note's voice eventually.)

- Voice: loose five-to-six-beat unrhymed line.
- Names: familiar Latinate spellings.
- δμώς/δμῳή rendered "slave/slave-woman" throughout.
- Untranslatable puns shadowed, not dropped ("Odysseus, Man at Odds" for
  ὀδυσσάμενος).
- Source: Murray 1919 Loeb via Perseus, with its three athetized omissions
  and two transposed pairs (3.304–305, 14.63–64) kept faithfully.

## 5. The independence question: measured overlap with prior translations

(Analysis run 2026-08-08 in response to the HN thread's "re-synthesis of
existing translations" objection. Method: lowercase, strip punctuation and
possessives, normalize Latin↔Greek proper names (Ulysses→Odysseus etc.),
then measure (a) the fraction of the translation's word n-grams appearing
anywhere in each comparison text and (b) maximal verbatim shared runs.
Comparison texts: Murray 1919 (Loeb — the facing translation of the exact
Greek source used), Butcher & Lang 1879, Butler 1900, Cowper 1791, Pope
1725, and Fagles 1996 (from the user's own copy; statistics only, text
never redistributed). Human-vs-human pairs measured with the identical
method as controls.)

Findings:

| pair | 5-gram overlap | 8-gram | runs ≥12 words | longest run |
|---|---|---|---|---|
| This translation vs Murray | 8.9% | 2.3% | 170 | 29 |
| This translation vs Butcher & Lang | 5.2% | 0.9% | 46 | 22 |
| This translation vs Butler | 1.6% | 0.1% | — | 12 |
| This translation vs Cowper | 0.2% | 0.0% | — | 9 |
| This translation vs Pope | 0.02% | 0.0% | — | 6 |
| **This translation vs Fagles** | **1.7%** | **0.2%** | 5 | **14** |
| **This translation vs Lattimore (1967)** | **6.2%** | **1.1%** | **62** | **24** |
| This translation vs Palmer (1891) | 3.8% | 0.6% | 30 | 19 |
| **Control: Butcher & Lang vs Murray** | **13.6%** | **4.5%** | **476** | **32** |
| Control: Butler vs Murray | 1.7% | 0.2% | 10 | 22 |
| Control: Cowper vs Pope | 0.1% | 0.0% | — | 8 |
| Control: Murray vs Fagles | 0.8% | 0.04% | 1 | 14 |
| Control: Butcher & Lang vs Fagles | 0.5% | 0.02% | 0 | 10 |
| Control: Butler vs Fagles | 0.5% | 0.02% | 0 | 11 |
| Control: Murray vs Palmer | 4.5% | — | 52 | 20 |
| Control: Butcher & Lang vs Palmer | 2.3% | — | 18 | 18 |
| Control: Butler vs Palmer | 0.9% | — | — | 12 |
| Control: Murray vs Lattimore | 3.5% | 0.4% | 23 | 21 |
| Control: Butcher & Lang vs Lattimore | 2.1% | 0.2% | 11 | 14 |
| Control: Palmer vs Lattimore | 1.7% | 0.1% | 3 | 15 |
| Control: Fagles vs Lattimore | 1.1% | 0.1% | 3 | 13 |

- The translation's *highest* overlap (with Murray, the most literal prior
  translation of the very same Greek text, and certainly present in
  training data via Perseus) is well *below* the overlap between two
  independent human literal translations of that text (Butcher & Lang vs
  Murray: 13.6% vs 8.9% at 5-grams; 476 vs 170 long shared runs).
- Stitching test: against the union of all eight prior translations at
  once (Lattimore and Fagles included), 81.6% of this translation's
  5-grams and 95.7% of its 8-grams appear in none of them.
- Lattimore (with Fagles, the pair the HN thread named): 6.2% of 5-grams
  shared, 62 runs of 12+ words (11 of 16+), longest 24 words (2.261ff,
  Telemachus washing his hands in the gray salt water before prayer).
  This is the highest overlap of any *modern* translation measured, and —
  unlike the Murray/Palmer/Fagles rows — the translation tops the human
  panel against Lattimore (Murray manages 3.5%). State this plainly, then
  give the two readings side by side: (a) Lattimore is the panel's only
  line-for-line literal verse translation in modern register — the same
  method, so highest convergence is what the literalness-not-lineage
  theory *predicts*; the panel contains no human translation of matched
  method to serve as the true control. (b) Read uncharitably as
  influence, the magnitude is still half of ordinary human-human literal
  convergence (Butcher & Lang vs Murray: 13.6%, 476 runs, 99 of 16+ vs
  62 and 11 here), and equal to Murray-vs-Palmer's 11 runs of 16+ words.
  Decisive against "mishmash of Lattimore and Fagles" specifically: this
  translation resembles Murray (8.9%) *more* than Lattimore (6.2%) and
  Fagles barely at all (1.7%) — the ordering tracks how literal each
  predecessor is, not how famous.
- Fagles specifically (the translation the HN thread accused, alongside
  Lattimore): 1.7% of 5-grams shared, longest verbatim run 14 words —
  and that same 14-word run ("give him a two-edged sword and sandals for
  his feet and send him," 1.113ff Athena on Telemachus) is *also* shared
  verbatim between Murray 1919 and Fagles. No run of 16+ words exists.
  Register caveat to state honestly: this translation's overlap with
  Fagles (1.7%) is ~2–3× the archaic-register controls' (0.5–0.8%),
  plausibly because both are modern English while Murray/Butcher & Lang
  are thee/thou prose — the clean control would be another modern
  translation (Wilson, Lombardo), not yet measured. Even read
  uncharitably as influence rather than shared register, the ceiling is
  a fraction of ordinary human-human literal convergence (13.6%).
- Bonus negative control: against Fagles's *Iliad* (his voice, different
  poem), this translation shares 0.30% of 5-grams (longest run 8 words,
  all stock formulas) vs Murray's-Odyssey-to-Fagles's-Iliad baseline of
  0.20% — no detectable Fagles house style.
- Palmer 1891 (plain-prose literal, from an archive.org scan mislabeled
  as "Lattimore 1967" — the OCR text is unmistakably Palmer: "Speak to
  me, Muse, of the adventurous man," "clear-eyed Athene," "discreet
  Telemachus") partially answers the register caveat above: Palmer
  writes plain modern-ish English with no thee/thou, yet this
  translation overlaps him at 3.8% of 5-grams — *below* the
  Murray-vs-Palmer human control (4.5%). Even against a plain-register
  literal human translation, the work sits inside the human convergence
  band. (Palmer OCR noise slightly depresses all Palmer rows equally.)
- Reading: overlap tracks *literalness of method*, not lineage. Two
  translators (human or machine) rendering the same Greek line word-for-
  word converge; that convergence is a property of the genre, and this
  translation sits inside — below the middle of — the human range.
- Honest caveats for the note: Fitzgerald/Wilson not yet measured
  (copyright; pending user-supplied copies); Lattimore normalization maps
  his Greek-style spellings (Telemachos, Kirke, Ithaka…) to the Latinate
  forms before comparison so spelling doesn't mask overlap. The longest verbatim
  run shared with Murray is real and worth citing as an example (4.540ff,
  29 words, "...my fill of weeping and writhing, then the unerring old man
  of the sea said to me..."), against the human-human control's longest of
  32. Butler's file shares a 60-word run with Butcher & Lang only because
  Butler's preface *quotes* them — a nice illustration of what actual
  copying looks like versus convergence.
- Scripts: tools/overlap_analysis.py and tools/overlap_runs.py (comparison
  texts downloaded from Gutenberg/Scaife at run time; paths inside point at
  the session scratchpad and need adjusting to rerun). Rerun against
  Lattimore et al. when copies are available.
