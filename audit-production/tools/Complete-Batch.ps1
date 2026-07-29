[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$BatchId
)

throw 'Complete-Batch.ps1 is obsolete. Use Finalize-Batch.ps1 with a validated adjudication-result.json sidecar.'

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $auditRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$entries = @(Get-Content -LiteralPath $ledgerPath | ForEach-Object { $_ | ConvertFrom-Json })
$matches = @($entries | Where-Object batch_id -eq $BatchId)
if ($matches.Count -ne 1) { throw "Unknown or duplicate batch '$BatchId'." }
$entry = $matches[0]
if ($entry.status -notin @('awaiting_adjudication', 'adjudicating')) {
    throw "Cannot complete a batch while status is '$($entry.status)'."
}
if ($entry.review.reviewer_1_status -ne 'complete' -or $entry.review.reviewer_2_status -ne 'complete') {
    throw 'Both independent reviews must be registered before completion.'
}

$requiredArtifacts = @(
    $entry.artifacts.reviewer_1,
    $entry.artifacts.reviewer_2,
    $entry.artifacts.adjudication,
    $entry.artifacts.report,
    $entry.artifacts.manifest
)
foreach ($relativePath in $requiredArtifacts) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relativePath))) {
        throw "Required artifact is missing: '$relativePath'."
    }
}

$sourceChecks = [ordered]@{
    greek = @((Join-Path $repoRoot $entry.sources.greek_path), $entry.sources.greek_sha256)
    translation = @((Join-Path $repoRoot $entry.sources.translation_path), $entry.sources.translation_sha256)
    formula = @((Join-Path $repoRoot $entry.sources.formula_path), $entry.sources.formula_sha256)
}
foreach ($name in $sourceChecks.Keys) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceChecks[$name][0]).Hash
    if ($actual -ne $sourceChecks[$name][1]) { throw "Source hash changed for $name." }
}

$manifest = Get-Content -LiteralPath (Join-Path $repoRoot $entry.artifacts.manifest) -Raw | ConvertFrom-Json
$batchDirectory = Join-Path $repoRoot $entry.artifacts.batch_directory
$sampleDirectory = Join-Path $batchDirectory 'sample'
$bookNumber = '{0:D2}' -f $entry.book
$lineRange = '{0:D3}-{1:D3}' -f $entry.start_line, $entry.end_line
$artifactChecks = [ordered]@{
    greek = Join-Path $sampleDirectory "greek-book-$bookNumber-lines-$lineRange.txt"
    translation = Join-Path $sampleDirectory "translation-book-$bookNumber-lines-$lineRange.md"
    notes = Join-Path $sampleDirectory "translation-notes-lines-$lineRange.md"
    formula = Join-Path $sampleDirectory 'formula-register.md'
    rubric = Join-Path $batchDirectory 'rubric.md'
    calibration = Join-Path $batchDirectory 'reviewer-calibration.md'
}
foreach ($name in $artifactChecks.Keys) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifactChecks[$name]).Hash
    if ($actual -ne $manifest.prepared_artifact_sha256.$name) {
        throw "Prepared artifact hash changed for $name."
    }
}

$total = $Critical + $Major + $Moderate + $Minor
$entry.metrics.critical = $Critical
$entry.metrics.major = $Major
$entry.metrics.moderate = $Moderate
$entry.metrics.minor = $Minor
$entry.metrics.total_findings = $total
$entry.metrics.findings_per_100 = [math]::Round(100 * $total / $entry.expected_record_count, 2)
$entry.metrics.reviewer_jaccard = $ReviewerJaccard
$entry.review.adjudication_status = 'complete'
$entry.status = 'complete'

$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{
    BatchId = $BatchId
    Status = $entry.status
    Findings = $total
    RatePer100 = $entry.metrics.findings_per_100
    ReviewerJaccard = $ReviewerJaccard
} | Format-Table -AutoSize
