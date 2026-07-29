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
$matches = @($entries | Where-Object batch_id -eq $BatchId)
if ($matches.Count -ne 1) { throw "Unknown or duplicate batch '$BatchId'." }
$entry = $matches[0]
if ($entry.status -ne 'adjudicating') { throw "Batch status must be adjudicating, not '$($entry.status)'." }

$requiredArtifacts = @($entry.artifacts.reviewer_1, $entry.artifacts.reviewer_2,
    $entry.artifacts.adjudication, $entry.artifacts.adjudication_result,
    $entry.artifacts.report, $entry.artifacts.manifest)
foreach ($relativePath in $requiredArtifacts) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relativePath))) {
        throw "Required artifact is missing: '$relativePath'."
    }
}

$manifestPath = Join-Path $repoRoot $entry.artifacts.manifest
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash -ne $entry.integrity.manifest_sha256) {
    throw 'The prepared manifest changed after it was anchored in the ledger.'
}
foreach ($reviewer in 1..2) {
    $reviewPath = Join-Path $repoRoot $entry.artifacts."reviewer_$reviewer"
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $reviewPath).Hash -ne
        $entry.integrity."reviewer_${reviewer}_sha256") {
        throw "Registered Reviewer $reviewer output changed before completion."
    }
}

$sourceChecks = [ordered]@{
    greek = @((Join-Path $repoRoot $entry.sources.greek_path), $entry.sources.greek_sha256)
    translation = @((Join-Path $repoRoot $entry.sources.translation_path), $entry.sources.translation_sha256)
    formula = @((Join-Path $repoRoot $entry.sources.formula_path), $entry.sources.formula_sha256)
}
foreach ($name in $sourceChecks.Keys) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $sourceChecks[$name][0]).Hash -ne $sourceChecks[$name][1]) {
        throw "Source hash changed for $name."
    }
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.batch_id -ne $entry.batch_id -or $manifest.book -ne $entry.book -or
    $manifest.start_line -ne $entry.start_line -or $manifest.end_line -ne $entry.end_line -or
    $manifest.record_count -ne $entry.expected_record_count) {
    throw 'Manifest identity or record metadata differs from the ledger.'
}
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
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $artifactChecks[$name]).Hash -ne
        $manifest.prepared_artifact_sha256.$name) {
        throw "Prepared artifact hash changed for $name."
    }
}

$resultPath = Join-Path $repoRoot $entry.artifacts.adjudication_result
$result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
if ($result.schema_version -ne 1 -or $result.batch_id -ne $entry.batch_id -or
    $result.record_count -ne $entry.expected_record_count) {
    throw 'Adjudication result identity, schema, or record count is invalid.'
}
$allowedSeverities = @('CRITICAL', 'MAJOR', 'MODERATE', 'MINOR')
$allowedCategories = @('MISTRANSLATION', 'OMISSION', 'ADDITION', 'GRAMMAR',
    'AMBIGUITY', 'LEXICAL', 'FORMULA', 'REGISTER', 'LINEATION')
$idPrefix = 'O{0:D2}-{1:D3}-{2:D3}-A-' -f $entry.book, $entry.start_line, $entry.end_line
$ids = [System.Collections.Generic.HashSet[string]]::new()
foreach ($finding in @($result.findings)) {
    if ($finding.id -notmatch "^$([regex]::Escape($idPrefix))\d+$") { throw "Invalid finding ID '$($finding.id)'." }
    if (-not $ids.Add($finding.id)) { throw "Duplicate finding ID '$($finding.id)'." }
    if ($finding.severity -notin $allowedSeverities) { throw "Invalid severity for '$($finding.id)'." }
    if ($finding.category -notin $allowedCategories) { throw "Invalid category for '$($finding.id)'." }
}
$adjudicationPath = Join-Path $repoRoot $entry.artifacts.adjudication
$adjudicationText = Get-Content -LiteralPath $adjudicationPath -Raw
$markdownRows = @([regex]::Matches($adjudicationText,
    '(?m)^\|\s*(O\d{2}-\d{3}-\d{3}-A-\d+)\s*\|\s*[^|]+\|\s*([A-Z]+)\s*\|\s*([A-Z]+)\s*\|') |
    ForEach-Object { [pscustomobject]@{ Id=$_.Groups[1].Value; Category=$_.Groups[2].Value; Severity=$_.Groups[3].Value } })
if ($markdownRows.Count -ne @($result.findings).Count) {
    throw 'Adjudication Markdown and JSON contain different finding counts.'
}
foreach ($finding in @($result.findings)) {
    $row = @($markdownRows | Where-Object Id -eq $finding.id)
    if ($row.Count -ne 1 -or $row[0].Category -ne $finding.category -or $row[0].Severity -ne $finding.severity) {
        throw "Markdown and JSON disagree for finding '$($finding.id)'."
    }
}
$unresolvedCount = @([regex]::Matches($adjudicationText, '\|\s*\*\*(?:Uncertain|Unresolved)\*\*\s*\|')).Count
if ($result.unresolved_count -isnot [long] -or $result.unresolved_count -lt 0 -or
    $result.unresolved_count -ne $unresolvedCount) {
    throw 'Invalid unresolved_count or disagreement with adjudication Markdown.'
}

$proposalSets = @{}
foreach ($reviewer in 1..2) {
    $reviewText = Get-Content -LiteralPath (Join-Path $repoRoot $entry.artifacts."reviewer_$reviewer") -Raw
    $reviewIds = @([regex]::Matches($reviewText, "(?m)^\|\s*(R$reviewer-\d+)\s*\|") | ForEach-Object { $_.Groups[1].Value })
    $proposalMap = @($result.reviewer_proposals."reviewer_$reviewer")
    $mappedIds = @($proposalMap | ForEach-Object { $_.review_id })
    if ((($reviewIds | Sort-Object) -join ',') -ne (($mappedIds | Sort-Object) -join ',')) {
        throw "Reviewer $reviewer proposal map does not match its firm finding IDs."
    }
    if (@($proposalMap | Where-Object { -not $_.proposal_key }).Count) {
        throw "Reviewer $reviewer proposal map contains an empty key."
    }
    $proposalSets[$reviewer] = @($proposalMap.proposal_key | Sort-Object -Unique)
}
$union = @($proposalSets[1] + $proposalSets[2] | Sort-Object -Unique)
$intersection = @($proposalSets[1] | Where-Object { $_ -in $proposalSets[2] })
$reviewerJaccard = if ($union.Count) { [math]::Round(100 * $intersection.Count / $union.Count, 2) } else { 100.0 }

$critical = @($result.findings | Where-Object severity -eq 'CRITICAL').Count
$major = @($result.findings | Where-Object severity -eq 'MAJOR').Count
$moderate = @($result.findings | Where-Object severity -eq 'MODERATE').Count
$minor = @($result.findings | Where-Object severity -eq 'MINOR').Count
$total = @($result.findings).Count
$rate = [math]::Round(100 * $total / $entry.expected_record_count, 2)
$reportText = Get-Content -LiteralPath (Join-Path $repoRoot $entry.artifacts.report) -Raw
if ($reportText -notmatch "(?m)^\|\s*Findings\s*\|\s*$total\s*\|" -or
    $reportText -notmatch "(?m)^\|\s*Findings per 100 records\s*\|\s*$rate\s*\|" -or
    $reportText -notmatch "(?m)^\|\s*Reviewer Jaccard agreement\s*\|\s*$reviewerJaccard%\s*\|") {
    throw 'Report metrics disagree with the derived adjudication metrics.'
}
$entry.metrics.critical = $critical
$entry.metrics.major = $major
$entry.metrics.moderate = $moderate
$entry.metrics.minor = $minor
$entry.metrics.total_findings = $total
$entry.metrics.findings_per_100 = $rate
$entry.metrics.reviewer_jaccard = $reviewerJaccard
$entry.review.adjudication_status = 'complete'
$entry.integrity.adjudication_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $adjudicationPath).Hash
$entry.integrity.adjudication_result_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $resultPath).Hash
$entry.integrity.report_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot $entry.artifacts.report)).Hash
$entry.status = 'complete'

$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{ BatchId=$BatchId; Status=$entry.status; Findings=$total;
    RatePer100=$entry.metrics.findings_per_100; ReviewerJaccard=$entry.metrics.reviewer_jaccard } |
    Format-Table -AutoSize
