[CmdletBinding()]
param(
    [string]$CalibrationVersion = 'semantic-only-formula-automation-v1'
)

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$rubricHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $auditRoot 'rubric.md')).Hash
$calibrationHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $auditRoot 'reviewer-calibration.md')).Hash
$entries = @(Get-Content -LiteralPath $ledgerPath | ForEach-Object { $_ | ConvertFrom-Json })

foreach ($entry in $entries) {
    if ($entry.status -eq 'planned') {
        $entry.calibration_version = $CalibrationVersion
        $entry.rubric_sha256 = $rubricHash
        $entry.calibration_sha256 = $calibrationHash
    }
}

$temporaryLedger = "$ledgerPath.tmp"
$entries | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

[pscustomobject]@{
    PlannedEntries = @($entries | Where-Object status -eq 'planned').Count
    CalibrationVersion = $CalibrationVersion
    RubricSha256 = $rubricHash
    CalibrationSha256 = $calibrationHash
} | Format-List
