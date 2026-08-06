# Project Memory — Odyssey Semantic Audit

Authoritative as of 2026-08-06.

## Completed audit

- The systematic production semantic audit of the complete *Odyssey* is finished.
- Corpus coverage: 12,107 / 12,107 aligned Greek and English records (100%).
- Ledger coverage: 60 / 60 units across Books 1–24.
- Adjudicated findings: 313 total — 58 `MODERATE`, 255 `MINOR`, 0 `MAJOR`, and 0 `CRITICAL`.
- The consolidated primary-translator handoff is [whole-poem-findings.md](whole-poem-findings.md).
- The authoritative machine state is [ledger.jsonl](ledger.jsonl), and the generated coverage summary is [status.md](status.md).
- The audit-completion checkpoint is `460c88eefe0da05631ec774a37227e3f85c26486` (`Complete production semantic audit through Odyssey Book 24`).

## Audit method that must be preserved

- Every production batch used two independent sealed semantic reviews followed by a separate adjudication.
- Review covered the Greek, translation, notes, rubric, and contemporaneous calibration.
- Firm findings remained separate from below-threshold concerns.
- Fixed-wording-only `FORMULA` deviations were excluded after the semantic-only production control took effect because automation owns that lane.
- Ledger transitions ran serially; independent reviews could run in parallel.
- Greek and translation source files were not modified during the audit itself.
- Batch artifacts, source hashes, adjudication schemas, report metrics, and Git scope were verified before checkpoints.

## Preserved historical exceptions

- Three older proposals remain explicitly unresolved and excluded from finding totals: two in `odyssey-01-156-444` and one in `odyssey-14-001-177`.
- Four historical translation-anchor mismatches remain for the two Book 1 units and two Book 2 units. They predate the final pass; all later Greek and translation anchors verified cleanly.
- The two pilot units and early legacy Book 1 unit retain their historical formula-policy totals even though later semantic batches excluded fixed-wording-only formula deviations.

## Post-audit correction state

- All 188 adjudicated translator-note corrections were drafted, applied, and checked off in [findings-worklist.md](findings-worklist.md).
- The correction set and historical before/after record live under [note-corrections](note-corrections/README.md).
- Note-correction checkpoint: `a66c42d` (`Apply 188 adjudicated note corrections from the whole-poem audit`).
- Corrected EPUB, AZW3, and PDF editions were regenerated in checkpoint `22aec66` (`Regenerate EPUB/AZW3/PDF editions with corrected notes`).

## Next review stage

Claude Fable, the primary translator, should review the entire findings handoff, using [findings-worklist.md](findings-worklist.md) as the execution map and the linked batch adjudications whenever a one-line summary is insufficient.

The remaining 125 findings are grouped as follows:

- 33 moderate verse findings: meaning-altering and expected to be fixed in nearly all cases, while preserving meter and diction.
- 33 systemic-policy findings: eight poem-wide decisions to make once and apply consistently.
- 59 discretionary minor verse findings: legitimate shading calls for translator judgment.

Do not automatically apply these remaining verse or policy findings without Claude Fable's review. Preserve unrelated worktree changes, and do not push checkpoints unless explicitly requested.
