# Odyssey Production Fidelity Audit

This directory tracks the systematic audit of all 24 books. The corpus has
12,107 aligned Greek and English verse records. Two pilot units covering 377
records are complete; 58 production batches cover the remaining 11,730.

## Controls

- Every batch stays within one book and uses the shared rubric and calibration.
- Two reviewers work independently and cannot inspect `reviews/`.
- Adjudication begins only after both reviewer reports are saved.
- Only adjudicated findings enter book and corpus totals.
- Source hashes and exact Greek/English line-label alignment are verified per batch.
- Reviewer analysis may run in parallel, but ledger transition commands must be run serially.

## Commands

Initialize the deterministic ledger once (the command refuses to overwrite live state):

```powershell
.\audit-production\tools\Initialize-Audit.ps1
```

Prepare one planned batch:

```powershell
.\audit-production\tools\Prepare-Batch.ps1 -BatchId odyssey-01-156-444
```

Register each saved independent review, then complete the batch only after the
adjudication and report exist:

```powershell
.\audit-production\tools\Register-Review.ps1 -BatchId odyssey-01-156-444 -Reviewer 1
.\audit-production\tools\Register-Review.ps1 -BatchId odyssey-01-156-444 -Reviewer 2
.\audit-production\tools\Start-Adjudication.ps1 -BatchId odyssey-01-156-444
.\audit-production\tools\Finalize-Batch.ps1 -BatchId odyssey-01-156-444
```

`ledger.jsonl` is the machine-readable workflow record. Batch artifacts live
under `batches/<batch-id>/`.

Regenerate the human-readable coverage summary with:

```powershell
.\audit-production\tools\Build-StatusReport.ps1
```
