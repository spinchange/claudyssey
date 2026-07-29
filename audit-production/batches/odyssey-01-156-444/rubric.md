# Fidelity Review Rubric

## Scope

Evaluate semantic fidelity to the supplied Greek passage and its English translation.
Read in syntactic units spanning line boundaries. The translation deliberately
uses one English verse for each Greek verse and a loose five-to-six-beat line;
do not flag defensible poetic recasting merely because it is not literal.

The translator's notes explain choices but do not establish that those choices
are correct. Other English translations are not a gold standard.

## Finding categories

- `MISTRANSLATION`: source meaning is materially changed or reversed.
- `OMISSION`: meaningful source content is absent without compensation nearby.
- `ADDITION`: the English asserts material content not supported by the Greek.
- `GRAMMAR`: agency, relationship, negation, tense, aspect, mood, or scope changes.
- `AMBIGUITY`: the English resolves a consequential Greek ambiguity too narrowly.
- `LEXICAL`: significant denotation or connotation is weakened or displaced.
- `FORMULA`: the English deviates from the authoritative formula register or
  materially mishandles a registered or repeated Homeric formula.
- `REGISTER`: consequential change in social, rhetorical, or character voice.
- `LINEATION`: one-to-one lineation causes a meaning or attachment distortion.

## Severity

- `CRITICAL`: reverses the action, agency, negation, or central proposition.
- `MAJOR`: loses or adds an important proposition, relationship, or poetic effect.
- `MODERATE`: meaningful local distortion that should probably be revised.
- `MINOR`: real but limited semantic or project-policy deviation with little
  downstream effect; revision may still be required by an explicit project rule.

Do not report mere alternative possibilities as errors. Use `confidence` from
0.00 to 1.00, and keep lower-confidence interpretive concerns separate.

`confidence` means the probability that the proposed difference is a material
fidelity problem, not merely confidence that the Greek and English use
different words or constructions. A firm finding normally requires confidence
of at least 0.75. Put plausible concerns from 0.50 through 0.74, or concerns
whose materiality remains uncertain, in the secondary table described below.
Omit weaker possibilities.

## Decision rules

### Generic plurals and quantifiers

A Greek bare plural may be generic even when it has no expressed equivalent of
English "all." Do not treat an added universal such as "all," "every," or
"always" as an automatic `ADDITION`. Report it as a firm finding only when the
context makes an exhaustive reading materially stronger than the likely Greek
scope. When both generic and exhaustive readings remain viable, place the case
in the secondary table and do not count it as an error.

### Speech acts

Evaluate what an utterance does as well as the topic it mentions. If the
English retains the general act of speaking but loses consequential force such
as ordering, forbidding, warning, promising, requesting, or swearing, classify
the primary problem as `MISTRANSLATION`. Use `GRAMMAR` when the distortion is
principally caused by mood, negation, agency, or another grammatical relation,
and `REGISTER` only when the action remains intact but its social or rhetorical
force changes. Assign one primary category rather than duplicating a finding.

### Compensation and wordplay

Judge compensation across the smallest coherent nearby passage, not only one
English line. Nonliteral wording may be justified when nearby language restores
the same semantic, rhetorical, formulaic, or sonic function with comparable
force. Preserving a pun, sound-link, meter, or lineation is relevant evidence,
but it does not by itself excuse the loss of consequential denotation. State
both the achieved compensation and the remaining loss, and set severity from
the net effect.

When the English introduces a different action or proposition that displaces
the Greek action, prefer `MISTRANSLATION` over `OMISSION`. Use `ADDITION` when
the source action remains represented but unsupported content is asserted
alongside it.

### Formula register

Treat the supplied formula register as authoritative project policy. Report a
departure from a fixed registered rendering as `FORMULA` even when the
alternative is semantically defensible or internally consistent. Ordinary
grammatical inflection required by English syntax is not a departure when the
registered lexical content and function remain intact. Use `MINOR` when the
violation has little semantic effect, and increase severity only when it also
causes a material loss.

## Required review format

Begin with a short overall assessment. Then provide a Markdown table:

| ID | Lines | Category | Severity | Confidence | Finding | Greek evidence | Suggested direction |
|---|---|---|---|---:|---|---|---|

Use one row per distinct issue and stable IDs (`R1-001`, `R2-001`, or `A-001`).
After the table, summarize counts by severity and identify three especially
successful renderings. Successful examples are calibration evidence, not part
of the error count.

When qualifying concerns exist, add a separate table headed `Concerns Considered`
with these columns:

| Lines | Confidence | Concern | Why not counted |
|---|---:|---|---|

This table is optional, contains no severity or finding IDs, and is excluded
from all error totals. Do not place below-threshold concerns in the required
findings table.
