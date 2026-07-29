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
if ($entry.status -ne 'awaiting_adjudication') {
    throw "Batch '$BatchId' must be awaiting adjudication, not '$($entry.status)'."
}
foreach ($reviewer in 1..2) {
    $relativePath = $entry.artifacts."reviewer_$reviewer"
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relativePath))) {
        throw "Required independent review is missing: '$relativePath'."
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot $relativePath)).Hash
    if ($actualHash -ne $entry.integrity."reviewer_${reviewer}_sha256") {
        throw "Registered Reviewer $reviewer output changed before adjudication."
    }
}

$entry.status = 'adjudicating'
$entry.review.adjudication_status = 'in_progress'
$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{ BatchId = $BatchId; Status = $entry.status } | Format-Table -AutoSize
