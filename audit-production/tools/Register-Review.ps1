[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BatchId,

    [Parameter(Mandatory)]
    [ValidateSet(1, 2)]
    [int]$Reviewer
)

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $auditRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$entries = @(Get-Content -LiteralPath $ledgerPath | ForEach-Object { $_ | ConvertFrom-Json })
$matches = @($entries | Where-Object batch_id -eq $BatchId)
if ($matches.Count -ne 1) { throw "Unknown or duplicate batch '$BatchId'." }
$entry = $matches[0]
if ($entry.status -notin @('prepared', 'reviewing')) {
    throw "Cannot register a review while batch status is '$($entry.status)'."
}

$property = "reviewer_${Reviewer}_status"
if ($entry.review.$property -eq 'complete') {
    throw "Reviewer $Reviewer is already registered for '$BatchId'."
}
$reviewRelativePath = $entry.artifacts."reviewer_$Reviewer"
$reviewPath = Join-Path $repoRoot $reviewRelativePath
if (-not (Test-Path -LiteralPath $reviewPath)) {
    throw "Expected review file does not exist: '$reviewPath'."
}
$reviewText = Get-Content -LiteralPath $reviewPath -Raw
if ($reviewText -notmatch '\|\s*ID\s*\|\s*Lines\s*\|') {
    throw "Review file does not contain the required findings table header."
}
$findingTable = [regex]::Match($reviewText, '(?ms)^\|\s*ID\s*\|.*?(?=\r?\n\r?\n)')
if (-not $findingTable.Success) { throw 'Cannot isolate the required findings table.' }
$tableLines = @($findingTable.Value -split '\r?\n')
$findingIds = @($tableLines | Select-Object -Skip 2 | ForEach-Object {
    $cells = $_ -split '\|'
    if ($cells.Count -gt 2) { $cells[1].Trim() }
} | Where-Object { $_ })
if (@($findingIds | Where-Object { $_ -notmatch "^R$Reviewer-\d+$" }).Count) {
    throw "Reviewer $Reviewer findings table contains an invalid ID."
}
$reviewHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $reviewPath).Hash
$otherReviewer = if ($Reviewer -eq 1) { 2 } else { 1 }
$otherHashProperty = "reviewer_${otherReviewer}_sha256"
if ($entry.integrity.$otherHashProperty -and $entry.integrity.$otherHashProperty -eq $reviewHash) {
    throw 'Independent reviewer reports have identical hashes.'
}

$entry.review.$property = 'complete'
$hashProperty = "reviewer_${Reviewer}_sha256"
$entry.integrity.$hashProperty = $reviewHash
$bothComplete = $entry.review.reviewer_1_status -eq 'complete' -and
    $entry.review.reviewer_2_status -eq 'complete'
$entry.status = if ($bothComplete) { 'awaiting_adjudication' } else { 'reviewing' }

$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{ BatchId = $BatchId; Reviewer = $Reviewer; Status = $entry.status } |
    Format-Table -AutoSize
