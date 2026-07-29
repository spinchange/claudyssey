[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BatchId
)

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $auditRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$entries = @(Get-Content -LiteralPath $ledgerPath | ForEach-Object { $_ | ConvertFrom-Json })
$entry = @($entries | Where-Object batch_id -eq $BatchId)
if ($entry.Count -ne 1) {
    throw "Expected exactly one ledger entry for '$BatchId'; found $($entry.Count)."
}
$entry = $entry[0]
if ($entry.status -ne 'planned') {
    throw "Batch '$BatchId' must be planned, not '$($entry.status)'."
}

$batchDirectory = Join-Path $repoRoot $entry.artifacts.batch_directory
$sampleDirectory = Join-Path $batchDirectory 'sample'
$promptDirectory = Join-Path $batchDirectory 'prompts'
$reviewDirectory = Join-Path $batchDirectory 'reviews'
if (Test-Path -LiteralPath $batchDirectory) {
    throw "Batch directory already exists: '$batchDirectory'."
}

$currentHashes = [ordered]@{
    greek = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot $entry.sources.greek_path)).Hash
    translation = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot $entry.sources.translation_path)).Hash
    formula = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot $entry.sources.formula_path)).Hash
    rubric = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $auditRoot 'rubric.md')).Hash
    calibration = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $auditRoot 'reviewer-calibration.md')).Hash
}
$expectedHashes = [ordered]@{
    greek = $entry.sources.greek_sha256
    translation = $entry.sources.translation_sha256
    formula = $entry.sources.formula_sha256
    rubric = $entry.rubric_sha256
    calibration = $entry.calibration_sha256
}
foreach ($key in $currentHashes.Keys) {
    if ($currentHashes[$key] -ne $expectedHashes[$key]) {
        throw "Provenance mismatch for $key in batch '$BatchId'. Reinitialize intentionally before preparing new work."
    }
}

New-Item -ItemType Directory -Path $sampleDirectory, $promptDirectory, $reviewDirectory -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $auditRoot 'rubric.md') -Destination (Join-Path $batchDirectory 'rubric.md') -Force
Copy-Item -LiteralPath (Join-Path $auditRoot 'reviewer-calibration.md') -Destination (Join-Path $batchDirectory 'reviewer-calibration.md') -Force

& (Join-Path $PSScriptRoot 'Build-Sample.ps1') `
    -Book $entry.book `
    -StartLine $entry.start_line `
    -EndLine $entry.end_line `
    -SampleDirectory $sampleDirectory `
    -FormulaFileName 'formula-register.md'

$bookNumber = '{0:D2}' -f $entry.book
$lineRange = '{0:D3}-{1:D3}' -f $entry.start_line, $entry.end_line
$greekFile = "greek-book-$bookNumber-lines-$lineRange.txt"
$translationFile = "translation-book-$bookNumber-lines-$lineRange.md"
$notesFile = "translation-notes-lines-$lineRange.md"
$greekLabels = @(Get-Content -LiteralPath (Join-Path $sampleDirectory $greekFile) | ForEach-Object {
    if ($_ -match '^(\d+)\t') { [int]$Matches[1] }
})
$translationLabels = @(Get-Content -LiteralPath (Join-Path $sampleDirectory $translationFile) | ForEach-Object {
    if ($_ -match '^(\d+)\s{2}') { [int]$Matches[1] }
})
if (($greekLabels -join ',') -ne ($translationLabels -join ',')) {
    throw "Prepared Greek and English labels differ for '$BatchId'."
}
if ($greekLabels.Count -ne $entry.expected_record_count) {
    throw "Prepared record count $($greekLabels.Count) differs from expected $($entry.expected_record_count)."
}

$translationText = Get-Content -LiteralPath (Join-Path $sampleDirectory $translationFile) -Raw
$noteIds = @([regex]::Matches($translationText, '\[\^([^\]]+)\]') | ForEach-Object {
    $_.Groups[1].Value
} | Sort-Object -Unique)
$manifest = [ordered]@{
    schema_version = 1
    batch_id = $BatchId
    book = $entry.book
    start_line = $entry.start_line
    end_line = $entry.end_line
    record_count = $greekLabels.Count
    selected_labels = $greekLabels
    absent_labels = @($entry.absent_labels)
    cited_note_ids = $noteIds
    calibration_version = $entry.calibration_version
    rubric_sha256 = $entry.rubric_sha256
    calibration_sha256 = $entry.calibration_sha256
    prepared_artifact_sha256 = [ordered]@{
        greek = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $sampleDirectory $greekFile)).Hash
        translation = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $sampleDirectory $translationFile)).Hash
        notes = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $sampleDirectory $notesFile)).Hash
        formula = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $sampleDirectory 'formula-register.md')).Hash
        rubric = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $batchDirectory 'rubric.md')).Hash
        calibration = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $batchDirectory 'reviewer-calibration.md')).Hash
    }
}
$manifest | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $batchDirectory 'manifest.json') -Encoding utf8

$relativeBatch = $entry.artifacts.batch_directory -replace '\\', '/'
foreach ($reviewer in 1..2) {
    $prompt = @"
Act as independent Reviewer $reviewer for an Ancient Greek-to-English literary
translation fidelity audit.

Read these files completely:

- $relativeBatch/rubric.md
- $relativeBatch/reviewer-calibration.md
- $relativeBatch/sample/$greekFile
- $relativeBatch/sample/$translationFile
- $relativeBatch/sample/$notesFile
- $relativeBatch/sample/formula-register.md

Assess *Odyssey* $($entry.book).$($entry.start_line)-$($entry.end_line) directly
against the Greek under the supplied rubric and calibration. Work independently.
Do not inspect $relativeBatch/reviews or any other review. Do not modify files.
Return the required Markdown review using IDs R$reviewer-001 onward. Report
material fidelity issues, not preferences, and keep qualifying concerns only in
the non-counted `Concerns Considered` table. The automated formula audit owns
fixed-register wording differences; do not report those unless there is a
distinct material semantic or rhetorical loss.
"@
    Set-Content -LiteralPath (Join-Path $promptDirectory "reviewer-$reviewer.md") -Value $prompt -Encoding utf8
}

$adjudicatorPrompt = @"
Act as adjudicator for two independent Ancient Greek-to-English fidelity reviews
of *Odyssey* $($entry.book).$($entry.start_line)-$($entry.end_line).

Read the rubric, reviewer calibration, all files under $relativeBatch/sample/,
and $relativeBatch/reviews/reviewer-1.md plus reviewer-2.md. Check every
proposal directly against the Greek. Merge duplicates and classify each as
sustained, modified, uncertain, or rejected. Agreement is not proof.
Reject proposals based only on fixed-register wording because the automated
formula audit records those separately.

Return an overall assessment; a findings table using stable IDs
O$bookNumber-$lineRange-A-001 onward; rejected/unresolved proposals; severity totals;
Jaccard agreement; findings per 100 records; three successful renderings; and
any calibration implications. After the Markdown, return a fenced JSON object
with schema_version, batch_id, record_count, unresolved_count, a findings array
containing each stable id, severity, and category, and reviewer_proposals maps
for reviewer_1 and reviewer_2. Each proposal entry must contain its review_id
and a shared proposal_key that is identical when the reviews identify the same
issue. Do not supply Jaccard; completion derives it. Do not modify files.
"@
Set-Content -LiteralPath (Join-Path $promptDirectory 'adjudicator.md') -Value $adjudicatorPrompt -Encoding utf8

$entry.status = 'prepared'
$entry.integrity.manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $batchDirectory 'manifest.json')).Hash
$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{
    BatchId = $BatchId
    Status = $entry.status
    Records = $greekLabels.Count
    Notes = $noteIds.Count
    Directory = $entry.artifacts.batch_directory
} | Format-Table -AutoSize
