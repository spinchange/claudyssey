[CmdletBinding()]
param(
    [string]$LedgerPath = (Join-Path $PSScriptRoot '..\ledger.jsonl'),
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\whole-poem-findings.md')
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ledger = @(Get-Content -LiteralPath $LedgerPath | ForEach-Object { $_ | ConvertFrom-Json })
$incomplete = @($ledger | Where-Object { $_.status -ne 'complete' })
if ($incomplete.Count -ne 0) {
    throw "Whole-poem findings require a complete ledger; $($incomplete.Count) unit(s) remain incomplete."
}

$records = ($ledger | Measure-Object -Property expected_record_count -Sum).Sum
$findings = ($ledger | ForEach-Object { [int]$_.metrics.total_findings } | Measure-Object -Sum).Sum
$critical = ($ledger | ForEach-Object { [int]$_.metrics.critical } | Measure-Object -Sum).Sum
$major = ($ledger | ForEach-Object { [int]$_.metrics.major } | Measure-Object -Sum).Sum
$moderate = ($ledger | ForEach-Object { [int]$_.metrics.moderate } | Measure-Object -Sum).Sum
$minor = ($ledger | ForEach-Object { [int]$_.metrics.minor } | Measure-Object -Sum).Sum

$unresolved = 0
$unresolvedBatches = [System.Collections.Generic.List[object]]::new()
function Get-HandoffLink([string]$Path) {
    $normalized = $Path.Replace('\', '/')
    if ($normalized.StartsWith('audit-production/')) {
        return $normalized.Substring('audit-production/'.Length)
    }
    return "../$normalized"
}

foreach ($entry in $ledger) {
    if (-not $entry.artifacts.adjudication_result) { continue }
    $resultPath = Join-Path $repoRoot $entry.artifacts.adjudication_result
    if (-not (Test-Path -LiteralPath $resultPath)) { continue }
    $result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
    if ($result.unresolved_count -gt 0) {
        $unresolved += $result.unresolved_count
        $unresolvedBatches.Add([pscustomobject]@{
            BatchId = $entry.batch_id
            Count = $result.unresolved_count
        })
    }
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Odyssey Whole-Poem Adjudicated Findings')
$lines.Add('')
$lines.Add("This handoff is generated from the authoritative ledger and the sustained-finding tables in all 60 batch reports. It is intended for the primary translator's poem-wide review; the batch adjudications remain the detailed source of truth.")
$lines.Add('')
$lines.Add('| Measure | Value |')
$lines.Add('|---|---:|')
$lines.Add("| Audited records | $records |")
$lines.Add("| Completed units | $($ledger.Count) / $($ledger.Count) |")
$lines.Add("| Adjudicated findings | $findings |")
$lines.Add("| Critical | $critical |")
$lines.Add("| Major | $major |")
$lines.Add("| Moderate | $moderate |")
$lines.Add("| Minor | $minor |")
$lines.Add("| Historically unresolved proposals | $unresolved |")
$lines.Add('')
$lines.Add('## Review guidance')
$lines.Add('')
$lines.Add('- Treat each row below as an adjudicated correction candidate, not an automatic edit instruction.')
$lines.Add('- Consult the linked batch adjudication when the short summary does not preserve enough Greek or contextual detail.')
$lines.Add('- Fixed-wording-only formula deviations were excluded once the semantic-only production control took effect; the two pilot units and early legacy Book 1 unit retain their authoritative historical totals.')
$lines.Add('- The historical unresolved proposals are listed separately and were excluded from finding totals.')
$lines.Add('')
$lines.Add('## Historical unresolved proposals')
$lines.Add('')
if ($unresolvedBatches.Count -eq 0) {
    $lines.Add('None.')
} else {
    foreach ($item in $unresolvedBatches) {
        $entry = $ledger | Where-Object { $_.batch_id -eq $item.BatchId } | Select-Object -First 1
        $adjudicationLink = Get-HandoffLink $entry.artifacts.adjudication
        $lines.Add("- [$($item.BatchId)/adjudication]($adjudicationLink): $($item.Count) unresolved proposal(s).")
    }
}
$lines.Add('')
$lines.Add('## Findings by book and batch')

$lastBook = 0
foreach ($entry in ($ledger | Sort-Object book, start_line)) {
    if ($entry.book -ne $lastBook) {
        $lines.Add('')
        $lines.Add("## Book $($entry.book)")
        $lastBook = $entry.book
    }

    $lines.Add('')
    $lines.Add("### $($entry.batch_id)")
    $lines.Add('')
    $adjudicationLink = Get-HandoffLink $entry.artifacts.adjudication
    $lines.Add("Detailed adjudication: [$($entry.artifacts.adjudication)]($adjudicationLink)")
    $lines.Add('')

    $reportPath = Join-Path $repoRoot $entry.artifacts.report
    $report = Get-Content -Raw -LiteralPath $reportPath
    $match = [regex]::Match($report, '(?ms)^## Sustained Findings\s*\r?\n(?<body>.*?)(?=^## |\z)')
    if (-not $match.Success) {
        $match = [regex]::Match($report, '(?ms)^## Result\s*\r?\n(?<body>.*?)(?=^## |\z)')
    }
    if (-not $match.Success) {
        throw "Could not locate a findings section in $reportPath"
    }

    $section = $match.Groups['body'].Value.Trim()
    foreach ($sectionLine in ($section -split '\r?\n')) {
        $lines.Add($sectionLine)
    }
}

$text = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText($OutputPath, $text, [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    OutputPath = (Resolve-Path $OutputPath).Path
    Records = $records
    Units = $ledger.Count
    Findings = $findings
    Unresolved = $unresolved
}
