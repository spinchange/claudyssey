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

(Analysis 2026-08-08, revised same day after adversarial review by a
GPT-5.6 reviewer, which caught a capped-run-length bug, paratext
contamination in the Gutenberg corpora, and several overclaims. Canonical
numbers and method now live in tools/independence_analysis.py — fully
reproducible from a public clone for the public-domain rows; Lattimore and
Fagles/Green rows require private copies via --lattimore/--fagles/--green. The public
page is docs/independence.html. Old ad-hoc scripts removed.)

Method: translation bodies only (prefaces/notes stripped), lowercased,
punctuation and possessives stripped, names normalized across traditions
incl. Lattimore's Greek spellings; n-gram overlap reported as the larger
of the two directions; maximal verbatim shared runs uncapped.

This translation vs (5-gram / runs>=12 / runs>=16 / longest):

- Murray 1919:        8.9% / 170 / 27 / 29
- Lattimore 1967:     6.3% /  64 / 11 / 24
- Green 2018:         5.3% /  49 /  3 / 20
- Butcher & Lang:     5.3% /  52 /  7 / 22
- Palmer 1891:        4.0% /  32 /  4 / 19
- Fagles 1996:        1.7% /   5 /  0 / 14
- Butler 1900:        1.6% /   0 /  0 / <12
- Cowper / Pope:      0.2% / 0.02% — nothing >=12

All 36 human-human pairs computed. Top: Murray-B&L 15.2% (492 runs, 105
>=16, longest 32) — a single outlier, and NOT a clean independence
baseline (Murray 1919 postdates B&L 1879 in the same archaizing literal
tradition). Next: Murray-Green 5.0%, Murray-Palmer 5.0%,
Murray-Lattimore 3.5%, Lattimore-Green 3.2%. Median human pair ~0.5%.

GREEN 2018 (added after the GPT review; user-supplied copy) closes the
matched-method gap: literal, modern register, line-matched verse. Green's
own affinity to Murray (5.0%) is the #2 human pair — elevated affinity to
literal predecessors is what matched method produces in humans too. And
Claudyssey-Green (5.3%, 49 runs, 3 >=16, longest 20) is statistically the
twin of Green-Murray (5.0%, 42 runs, 4 >=16, longest 21): the model
relates to the matched-method human as that human relates to his own
nearest predecessor. Residual: Claudyssey-Murray (8.9%) and -Lattimore
(6.3%) still run ~2x Green's affinities to the same texts (5.0%, 3.2%) —
candidate explanations are stricter method (same line count, same
word-order discipline, Murray's own Greek as source) and/or model
influence; undecomposable with these metrics, state both.

Honest framing (do not overclaim in the note):

- Three of this translation's affinities (Murray, Lattimore, B&L) exceed
  every human pair except Murray-B&L. High-percentile, said plainly.
  The numbers cannot decompose "same method, same Greek, same register"
  from "model influence"; no matched-method human control exists in the
  panel (Green now fills most of this gap; Wilson row still pending a measurable copy).
- What IS bounded: verbatim reuse. Union test vs all eight at once:
  79.5% of 5-grams / 95.1% of 8-grams / 65.8% of 4-grams appear in NONE (nine-text union incl. Green).
  Longest run with anyone: 29 words (Murray). Positive control: a
  deliberate 12-token splice of Murray+B&L+Lattimore scores 67% on the
  same union test vs the translation's 20.5%. ROUND-2 CORRECTION (GPT
  reran splices at multiple chunk sizes; verified exactly): pure 5-word
  splice scores 20.7% on the 5-gram test — indistinguishable from the
  translation's 20.5% — because sliding windows cross fragment
  boundaries. Correct scope: "strongly disfavors assembly from verbatim
  passages of ~8-12 words or longer; CANNOT exclude 4-6-word mosaics."
  Secondary observation, not proof: any pure sub-12-word mosaic yields
  ZERO runs >=12, vs the translation's 170 with Murray / 49 with Green —
  the long-run profile matches convergent translation (Green-Murray: 42),
  not concatenation; a mixture would land between and can't be excluded.
- Fagles, corrected round 2: "modest but not absent," never "no support
  at all." The 1.7% EXCEEDS every human-Fagles pairing (max: Lattimore
  1.1%, Green 1.0%) — state this unprompted. But: fraction of the
  Murray/Lattimore affinities, five runs >=12, none >=16, longest is a
  formula Fagles shares verbatim with Murray. Not a meaningful donor;
  minor influence not excludable.
- The convergence-magnet detail: the longest run shared with Fagles AND
  the longest shared with Green are the SAME passage — the repeated
  clothing-promise formula (14.516 -> 21.339, five occurrences), which
  this translation deliberately renders identically at each return per
  the formula rule. Where translations converge verbatim, they converge
  on Homer's own repetitions.
- Proem, word by word, round-2 posture (concede-then-bound, per review):
  argue from the Greek where true ("Tell me the man" bare accusative;
  "turnings" root-literal; only Murray+Lattimore use the "man of many _"
  frame — NOT B&L/Palmer, don't overcite), and concede the real echoes:
  "the man...the man" doubling parallels Fagles (Greek has one andra);
  "once he had" matches Fagles's construction; "holy citadel" is synonym
  substitution inside Lattimore's frame (consistent with independence,
  not evidence of it); mala dropped. Close with proportionality: the
  proem is the most famous-rendering-saturated line in Greek; one line
  cannot sustain a verdict on 124,000 words — the whole-book bounds do.
- What copying looks like: Butler's PG file shares a 253-word verbatim
  run with B&L — his preface quoting them. (First analysis said 60 —
  that was the search cap, caught in review.) Cleaned to bodies only,
  Butler-B&L collapses to 3 runs, longest 14. Quotation vs convergence.
- Fagles-Iliad cross-poem aside: 0.30% vs Murray's 0.20% — describe as
  "same order," never "statistically indistinguishable" (no uncertainty
  estimate).

Tone note (user feedback 2026-08-08): full disclosure yes, but written
as lab-notebook rigor, not confession — the first draft of the page's
provenance section "read like a confession." State corrections plainly,
once, without self-flagellating cadence.

For the translator's note eventually: use the strongest defensible
conclusion, roughly — "Across nine comparison texts we found no evidence
of construction by extensive verbatim reuse; exact-text affinity to
Fagles is weak; affinity to Lattimore is conspicuously higher and may
reflect matched method, model influence, or both; these tests cannot
exclude shorter-form, syntactic, semantic, or interpretive dependence —
the debts every translator owes predecessors."


## 6. Preregistered predictions: the Wilson row

(Recorded 2026-08-08, BEFORE any measurement of Wilson's translation.
The user is acquiring a print copy to scan; nothing of Wilson's text has
been ingested or measured as of this commit. The commit timestamp is the
notarization. When the row is run, report the outcome against these
predictions verbatim — hits and misses both — and do not revise this
section except to append results.)

Method identical to the rest of the panel: tools/independence_analysis.py
with --wilson, translation body only, name-normalized, directional-max
n-gram overlap, uncapped runs.

Predictions from the convergence account (overlap tracks literalness and
method, not fame):

1. Claudyssey vs Wilson, 5-gram: between 2.5% and 4.0%. Rationale:
   matched method (modern register, line-count discipline — the only
   major translation sharing the line-for-line constraint) pushes up;
   Wilson's deliberately plain, compressed diction — the most divergent
   idiom among the literalists — pushes down. Net: between Fagles (1.7%)
   and Green (5.3%).
2. Ordering preserved: Claudyssey-Wilson lands BELOW Claudyssey-Green
   and far below Claudyssey-Murray (8.9%); the Claudyssey row ordering
   stays Murray > Lattimore > Green ≈ B&L > Palmer > Wilson > Fagles.
3. Longest shared run with Wilson: under 20 words; no run of 20+.
4. Human controls: Wilson-Murray between 1.5% and 3.0%; Wilson's
   affinities to the whole panel run below Green's corresponding ones
   (her compression cuts n-gram continuity everywhere).
5. Fame check (the Green-vs-Fagles inference, second trial): Wilson is
   the most-discussed translation of the century; if affinity followed
   fame she would rank near the top of the Claudyssey rows. Predicted:
   she ranks in the lower middle, per (2).

Falsification, stated in advance: if Claudyssey-Wilson exceeds Green's
5.3%, or any shared run reaches 24+ words, the convergence account as
stated on the independence page needs revision, and the page gets
corrected — not the framing.

### Results (appended 2026-08-12, first measurement)

Scan: print copy, poem only (no back matter; no end marker needed),
OCR verified clean (curly apostrophes intact, no ligature splits).
Wilson = 98,750 tokens after normalization — shortest text in the
panel, consistent with her line-for-line compression. Caveat noted
before interpreting: the scan's running heads ("HOMER: THE ODYSSEY" /
book titles) are not stripped, unlike Palmer's; at ~420 pages this
depresses Wilson pairings by roughly 3% relative — far too small to
explain the misses below.

1. Claudyssey-Wilson 5-gram predicted 2.5–4.0%: **MISS, low.**
   Actual 1.39% — below the predicted floor and below Fagles (1.74%).
   (4g 4.29%, 6g 0.56%, 8g 0.10%.)
2. Ordering predicted Murray > Lattimore > Green ≈ B&L > Palmer >
   Wilson > Fagles: **PARTIAL MISS.** Wilson lands below Green and far
   below Murray (8.91%) as predicted, but she and Fagles swap: actual
   tail is … Palmer (3.98%) > Fagles (1.74%) > Wilson (1.39%). Wilson
   is the panel minimum, not second-from-last.
3. Longest shared run under 20 words: **HIT.** Longest is 13 words
   ("son of atreus why ask me this you have no need to know"); only
   one run ≥12 in the whole pairing, none ≥16.
4. Wilson-Murray predicted 1.5–3.0%: **MISS, low** — actual 0.89%.
   Wilson below Green's corresponding affinity across the panel:
   **HIT** for every text that rises above the noise floor (e.g.
   Murray 0.89% vs Green's 5.05%; Lattimore 0.99% vs 3.16%); the two
   pairings at the floor are a wash (Cowper 0.15% vs 0.13%, Pope
   0.01% vs 0.01%).
5. Fame check predicted lower middle: **MISS in the direction that
   strengthens the inference.** The most-discussed translation of the
   century ranks dead last in the Claudyssey rows. Second trial of
   the fame-vs-method inference: affinity does not track fame.

Falsification conditions: not triggered (1.39% < 5.3%; longest run
13 < 24). The convergence account survives, but the misses are
one-directional and shared by the human controls: everything touching
Wilson came in lower than predicted, including Wilson-vs-panel rows no
Claudyssey text participates in. The "compression cuts n-gram
continuity" mechanism was right and underweighted; the "matched
method (line discipline) pushes up" mechanism produced no visible
signal. Lesson for the translator's note: shared formal constraints
do not leave an n-gram fingerprint; shared diction does.

### Corrections (appended 2026-08-12, after adversarial cross-review)

A second-model adversarial review of the results above caught real
errors. Per the append-only rule the original text stands; this
section corrects it and its numbers are now canonical.

1. "Panel minimum" / "dead last" was a misreading of our own table.
   Wilson's row is the lowest among the modern translations, below
   Fagles, but Cowper (0.19%) and Pope (0.02%) sit below her. She is
   8th of 10, not 10th. Prediction 5 rescored: she landed lower than
   the predicted lower-middle (a miss in placement), and the anti-fame
   inference is supported but weaker than the original append claimed;
   see also the formula confound below.
2. "Every quantitative prediction missed low" (as echoed on the page
   draft) was a miscount: the longest-run prediction was numeric and
   HIT. Accurate tally: two range predictions missed low; ordering
   partial miss (Wilson/Fagles swapped); longest-run hit; the
   below-Green-everywhere prediction failed at one pairing (see 3).
3. Prediction 4's second half is a partial miss, not a "HIT with a
   wash": Wilson-Cowper 0.149% is above Green-Cowper 0.130%, and the
   preregistration made no noise-floor exception, so scoring may not
   invent one.
4. The falsification thresholds were one-sided: only high-side
   surprises could trigger them. The low-side misses were never
   falsification-capable, and no claim of surviving a symmetric test
   should be made.
5. Method fix: the scan's 394 running page-head lines are now stripped
   in the loader (same body-only treatment as Palmer). Canonical
   post-fix numbers: Wilson 97,258 tokens (cleaned-corpus
   sha256:5222dcd4bd1e0b91; source PDF sha256:
   39a8078d2572f9a968601a7d19ad1a22582e2163d01dea5b130fd99398248aeb).
   Claudyssey-Wilson 5-gram 1.42% (directions 1.33/1.42), 4g 4.31%,
   6g 0.57%, 8g 0.10%, one run ≥12, longest 13. Wilson-Murray 0.91%.
   Butcher & Lang-Wilson 0.653%, which now rounds to 0.7%. Human-pair
   5-gram median (45 pairs) 0.83%; Claudyssey-row median 2.86%. No
   conclusion changes.
6. Disclosure: what the preregistration establishes is narrow — the
   predictions were made before any Wilson corpus entered the analysis
   pipeline or any full-corpus statistic was computed. They were not
   translator-blind: an internal note dated July 18-21 (before the
   Aug 8 prereg) contains Wilson's proem and analysis of her diction,
   meter, and line-count constraint. And the model coauthor's latent
   training exposure to her text is unknown (the page's own opening
   premise), so "corpus-blind" would overclaim too. "Nothing of
   Wilson's text has been ingested" was true of the measurement
   corpus, not of the authors' exposure. The public page now says so.
7. Confound worth carrying into the translator's note: Wilson
   deliberately varies Homer's repeated formulas where the Claudyssey
   (like Murray and Fagles) repeats them verbatim; that choice alone
   suppresses shared n-grams and runs, independent of fame or
   literalism. Her row is consistent with affinity-follows-method but
   is not a clean second trial of it.

## 7. Preregistered predictions: the Johnston row

(Recorded 2026-08-12, BEFORE any measurement of Johnston's translation.
A copy of Ian Johnston's Odyssey sits at corpus/johnston.txt, gitignored
like every in-copyright input; no overlap statistic, run, or token count
of it has been computed as of this commit. The public push of this
commit is the notarization. When the row is run, report the outcome
against these predictions verbatim — hits and misses both — and do not
revise this section except to append results.)

Disclosure, stated up front per the Wilson corrections: this
preregistration is not translator-blind and not exposure-blind. The
July 18-21 internal note contains Johnston's proem and analysis of his
diction; the pre-prediction inspection of the file itself was: first 25
lines, last 15 lines, total line count (16,098), and four structural
greps (book headers, bare page numbers, footnote brackets, tabs — all
zero). The model coauthor's latent training exposure is unknown and
plausibly HIGH: Johnston's text is freely mirrored across the open web,
which is precisely what makes this row informative — it separates
web-prevalence from print fame, and both from method.

Method identical to the panel: tools/independence_analysis.py with
--johnston, translation body only (the file is verifiably poem-only),
name-normalized, directional-max n-gram overlap, uncapped runs.

Known method profile (from the July note and public descriptions):
modern plain register, free verse, moderately literal but openly
expansive — 16,098 lines against the Greek's 12,110, no line-count
constraint, explanatory padding ("that's why he snatched away their
chance / of getting home someday").

Predictions from the convergence account (overlap tracks literalness
and diction, not fame and not raw web prevalence), with the Wilson
lesson applied (diction outweighs shared-constraint effects):

1. Claudyssey-Johnston, 5-gram: between 1.8% and 3.5%. Modern register
   and moderate literalism push up; expansion and free-verse phrasing
   dilute n-gram correspondence. Predicted slot: above Fagles (1.7%),
   below Palmer (4.0%).
2. Ordering: Murray > Lattimore > Green ≈ B&L > Palmer > Johnston >
   Fagles > Butler > Wilson, with Cowper and Pope below all.
3. Longest shared run: under 20 words; no run of 20+.
4. Human controls: Johnston-Murray between 1.5% and 3.0%; Johnston's
   panel affinities land above Wilson's corresponding ones (he does not
   compress) and below Green's (he is not tightly literal).
5. Web-prevalence check: Johnston's full text is plausibly the most
   training-available English Odyssey there is. Raw memorization
   predicts a top-tier row; the convergence account predicts the
   mid-lower slot in (2). Like the fame inference, a hit here is a
   consistent pattern, not an isolated-variable test, and will be
   reported with that caveat.

Adverse-evidence thresholds, one-sided by design and labeled as such
(low-side misses are informative about mechanism but cannot trigger
this clause): if Claudyssey-Johnston exceeds Green's 5.3%, or any
shared run reaches 24+ words, the convergence account as stated on the
independence page needs revision, and the page gets corrected — not
the framing.

### Results (appended 2026-08-12, first measurement, same day as prereg)

Johnston = 128,127 tokens after normalization (cleaned-corpus
sha256:a4c52babcf8a0c15; source txt sha256:
fb627016748f24e7f48fcf053231304674d502dd07f9784d92f69dc301bb67d1).
Prereg pushed as ece959d before the run.

1. Claudyssey-Johnston 5-gram predicted 1.8-3.5%, above Fagles and
   below Palmer: **HIT.** Measured 2.83% (directions 2.83/2.26);
   4g 7.16%, 6g 1.26%, 8g 0.26%.
2. Ordering: **FULL HIT, every position.** Murray 8.91 > Lattimore
   6.29 > Green 5.35 ≈ B&L 5.28 > Palmer 3.98 > Johnston 2.83 >
   Fagles 1.74 > Butler 1.58 > Wilson 1.42, Cowper and Pope below all.
3. Longest run under 20 words, no run of 20+: **MISS, HIGH — the
   first high-side miss in either preregistration.** A 21-word shared
   run exists: Phemius setting down the lyre to supplicate Odysseus
   (22.339-341, "the knees of laertes son odysseus so he set the
   hollow lyre down on the ground between the mixing bowl and"). A
   narrative passage occurring once in the poem, not a formula. 8 runs
   ≥12, one ≥16 (the 21). Below the 24-word adverse threshold, but
   this is now the longest run shared with any modern except
   Lattimore's 24, and longer than Johnston shares with any human
   (his max is 18, with Murray).
4. Johnston-Murray predicted 1.5-3.0%: **HIT** (2.66%). Above Wilson's
   and below Green's corresponding rows: **PARTIAL MISS.** Holds for
   all seven substantive texts; fails at Cowper on both sides
   (Johnston-Cowper 0.14 is below Wilson-Cowper 0.15 and above
   Green-Cowper 0.13), at Pope on the Green side (0.02 vs 0.01), and,
   more interestingly, at the Wilson pairing itself: Johnston-Wilson
   1.50 is nearly twice Green-Wilson 0.83. Two plain modern registers
   converge on each other; the prediction did not anticipate that.
5. Web-prevalence check: **HIT as pattern** (caveat as preregistered:
   consistent, not an isolated-variable test). The plausibly
   most-training-available English Odyssey lands sixth of eleven,
   exactly the predicted slot, not top-tier.

Adverse-evidence thresholds: not triggered (2.83% < 5.3%; 21 < 24).

Residual, for fairness: Claudyssey-Johnston 2.83% exceeds every
human-Johnston pairing (max Murray 2.66%), a 1.06x relative excess,
about the size of the Green-vs-Murray analog the page leans on, and
far smaller than the Wilson (1.4x) or Lattimore (1.8x) excesses.

Panel-wide updates with eleven priors: union test 5g 21.95% found
(78.1% in none), 4g 36.42%, 8g 5.17%. Human-pair 5g median (55 pairs)
0.97%; Claudyssey-row median (11 rows) 2.83%. Johnston's arrival
raises the human median from 0.83% because his rows against the
moderns are healthy mid-range values, which is itself evidence that
modern-register translations converge on each other.

### Corrections (appended 2026-08-12, after the third adversarial review)

The review that audited the Johnston revision found the results append
above defective in ways that matter. Originals stand per the
append-only rule; this section corrects and supersedes.

1. THE CORPUS WAS AN UNIDENTIFIED REVISION, AND IT MATTERS.
   corpus/johnston.txt carries no edition statement; it is a pre-2024
   web revision of a translation Johnston has revised repeatedly since
   2002. Against his current official text (VIU repository PDF,
   generated 2024-10-16, "This document is in the public domain";
   source sha256:
   e898722ff0982251c78d561f7fe6bb57ccd653c41e3503d2862884613748523e,
   cleaned corpus 128,466 tokens sha256:b74716133191e744, cleaning
   script tools/johnston_version_check.py), the row reads 5-gram 2.43%
   (dir 2.43/1.95), longest run 12, one run >=12, Murray control
   2.34%. The 21-word run does not exist in the 2024 text: Johnston
   revised the Phemius lines ("clasp the knee ... He set down the
   hollow lyre, left it on the ground"). The two Johnston versions
   share only 72.3% of their own 5-grams. Both readings are reported
   on the page: the run is revision-fragile, AND the old revision is
   the training-era text, so for exposure questions the 21-word match
   to it remains the finding. Range and ordering predictions hold
   against either version.
2. PROTOCOL AMENDMENT, binding on future rows: the preregistration
   must commit the source-file hash BEFORE measurement. This prereg
   committed only a line count and structural description; the hash
   arrived with the results, locking the predictions but not the
   corpus.
3. Prediction 4 was mis-scored: it failed at THREE pairings (Cowper
   violates both clauses: Johnston 0.141% < Wilson 0.149% and > Green
   0.130%; Pope on the Green side: 0.02% > 0.01%; and Wilson:
   Johnston-Wilson 1.50% > Green-Wilson 0.83%). "Holds for all seven
   substantive texts" was wrong; the correct count is six (Murray,
   Butler, Butcher & Lang, Palmer, Lattimore, Fagles). No noise-floor
   carve-outs.
4. Predictions 1, 2, and 5 were three descriptions of one outcome
   (Johnston's placement); the other ten rows' order was already
   known. "FULL HIT, every position" overstated; the honest statement
   is one measured placement satisfying three dependent preregistered
   descriptions.
5. The web-prevalence "check" is withdrawn as a test. Prevalence was
   never measured; the premise is unverified; and the version problem
   shows "Johnston" is not one text. Post-hoc interpretation only.
6. "Modern registers converge" is a hypothesis, not a result; of
   Johnston's eight above-median pairings, five involve non-modern
   texts. The median account is now descriptive on the page.
7. Johnston is PUBLIC DOMAIN (his own statement in the 2024 PDF), not
   in copyright as the page briefly claimed. Manifest and page fixed.
8. Chronology: Johnston was measured about two hours after the Wilson
   corrections merged, later the same day, not "days after."
9. The file's 16,098 lines include 23 blank separators; 16,075
   nonblank poem lines.
10. Panel-wide error caught in the same review, predating Johnston:
    Murray-Green is 5.055%, which rounds to 5.1%, not the 5.0% the
    page had displayed since Green joined the panel. Fixed everywhere,
    including the "5.3% vs 5.1%" matched-method comparison.
