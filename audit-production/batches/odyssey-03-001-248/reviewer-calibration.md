# Reviewer Calibration

## Purpose

Use these adjudicated examples to align reviewers on materiality, category,
severity, and confidence. A firm finding requires both a demonstrable
difference from the Greek and a material semantic, rhetorical, grammatical,
formulaic, or characterizing loss or addition. A wording difference alone is
not a finding.

Firm findings normally require `confidence >= 0.75`. Plausible cases whose
materiality remains uncertain belong under `Concerns Considered`, even when
the lexical difference itself is clear.

## Firm-Finding Anchors

| Lines | Decision | Category | Severity | Calibration point |
|---|---|---|---|---|
| 1.58-59 | Report | `LEXICAL` | `MODERATE` | “Would be glad to see” materially weakens `ἱέμενος`, Odysseus' urgent yearning. The nearby wish for death does not restore the lost force. |
| 1.62 | Report | `LEXICAL` | `MODERATE` | “At odds with” preserves sound-play but weakens `ὠδύσαο`, Zeus' anger or hostility. Wordplay does not compensate for consequential denotation. |
| 1.90-92 | Report | `MISTRANSLATION` | `MODERATE` | “Speak out to” preserves speaking but loses the instruction to forbid or warn off the suitors. Loss of operative speech force is mistranslation. |
| 9.381 | Report | `LEXICAL` | `MINOR` | “A great power breathed courage” transfers `μέγα` from the courage to its divine source. Divine intervention remains, so the shift is limited. |
| 9.389-390 | Report | `ADDITION` | `MINOR` | “Singed ... away” asserts complete destruction not stated by the Greek. The unsupported result is real but localized. |
| 9.464-466 | Report | `MISTRANSLATION` | `MODERATE` | Looking behind invents an action and replaces the rounding or turning of sheep while driving them. |
| 1.184 note | Report | `MISTRANSLATION` | `MODERATE` | “Copper out, iron in” reverses both commodities even though the verse is correct. Material claims in explanatory notes remain auditable. |
| 2.53-54 | Report | `GRAMMAR` | `MODERATE` | “Whoever comes and pleases her” shifts the dative of favor from Icarius to Penelope; count pronoun-reference shifts when they change consequential social agency. |
| 2.244-245 | Report | `GRAMMAR` | `MODERATE` | “Men who outnumber you” reverses comparative scope; count comparative/scope shifts when they change the force of a reply. |
| 2.383 note | Report | `MISTRANSLATION` | `MODERATE` | Saying Athena borrows the ship “as herself” misstates the disguise sequence; explanatory notes are findings when they alter narrative mechanics. |

## Automated Formula Anchors

These adjudicated findings remain authoritative examples, but the corpus-wide
formula scanner now owns them. Reviewers must not count them again unless the
passage also contains a distinct material semantic or rhetorical loss.

| Lines | Automated decision | Calibration point |
|---|---|---|
| 9.528, 536 | `FORMULA` violation | “Dark-haired” is defensible Greek but violates registered “with the blue-black hair.” |
| 1.191, 362 | `FORMULA` violation | “Serving-woman/women” violates fixed “handmaid/attendant women” vocabulary despite being broadly intelligible. |
| 1.420 | `FORMULA` violation | Naming Telemachus varies fixed “So he spoke,” though it preserves the proposition. |

## Non-Finding Anchors

| Lines | Decision | Reason |
|---|---|---|
| 1.21 | Do not report | “Until the day he reached” is defensible proleptic epic narration despite the prospective Greek construction. |
| 1.48 | Do not report | Athena's concern controls “my heart is on fire”; an irrelevant possible English association does not create material ambiguity. |
| 1.54 | Do not report | “Hold earth and heaven apart” is a coherent resolution of spatially flexible Greek. Fidelity does not preserve every possible reading. |
| 1.86-87 | Do not report | “That he shall return” is defensible after the gods' unerring plan, not a consequential modal change. |
| 1.120 | Do not report | “Be left standing” conventionally implies being kept waiting and compensates for `δηθά`. |
| 9.447 | Do not report | Idiomatic “old sweetheart” can mark familiarity rather than literal age and preserves tenderness. |
| 9.479 | Do not report | Nearby language makes the retributive sense of “Zeus has paid you” clear. Judge the coherent passage, not an isolated phrase. |
| 9.549 | Do not report | “No man might go cheated of his share” sufficiently represents an equal or due portion. |
| 9.562 | Do not report | “In their turn” adds an inconsequential sequencing nuance without changing action or agency. |
| 1.436 | Do not report | “He opened” defensibly continues with Telemachus as subject across coordinated actions. Do not infer an agency reversal merely because Homer permits an unmarked subject shift. |

## Below-Threshold Anchors

These belong only in `Concerns Considered` and receive no IDs or severities.

| Lines | Concern | Why not counted |
|---|---|---|
| 1.33 | “All evils” may be more exhaustive than bare plural `κάκʼ`. | Generic and exhaustive readings remain viable. |
| 9.444-445 | “My crowding thoughts” may not directly express shrewd or close thinking. | The density wordplay is meaningful and careful guile is established nearby, leaving material loss uncertain. |
| 1.280 | “Twenty oars” names equipment where Greek specifies twenty rowers. | “Man a ship” restores the crew, and a twenty-oared ship conventionally implies corresponding rowers. |
| 1.398 | “Slaves ... won” weakens the plunder force of `ληίσσατο`. | “Won” can still denote martial acquisition, while enslaved status and acquisition remain explicit. |

## Category And Severity Checks

- Use `MISTRANSLATION` when an event, proposition, or speech act is materially
  changed, including when a new action displaces the Greek action.
- Use `OMISSION` when meaningful content disappears without conflicting
  replacement content.
- Use `ADDITION` when the Greek action remains but unsupported material is
  asserted alongside it.
- Use `LEXICAL` when the event remains intact but force, denotation, or emphasis
  is materially weakened.
- Use `FORMULA` only for a material semantic or rhetorical mishandling of a
  registered recurrence. The automated lane owns fixed-wording departures.
- `MODERATE` means a meaningful local distortion that should normally be
  revised. `MINOR` means a real localized deviation with little downstream
  effect. Severity measures effect, not how easy the correction is.

## Final Review Check

- Read across line boundaries and judge compensation in the smallest coherent passage.
- Do not duplicate fixed-wording violations owned by the automated formula lane.
- Keep firm findings and below-threshold concerns in separate tables.
- Assign one primary category.
- Base confidence on the probability of a material problem, not merely certainty about the Greek.
- Do not count successful poetic recasting as an error.
- Audit material explanatory-note claims as well as the verse, but distinguish a
  false note from a correct translated line.
