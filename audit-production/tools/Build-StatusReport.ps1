[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$outputPath = Join-Path $auditRoot 'status.md'
$entries = @(Get-Content -LiteralPath $ledgerPath | ForEach-Object { $_ | ConvertFrom-Json })
$complete = @($entries | Where-Object status -eq 'complete')
$totalRecords = ($entries.expected_record_count | Measure-Object -Sum).Sum
$auditedRecords = ($complete.expected_record_count | Measure-Object -Sum).Sum
$totalFindings = ($complete.metrics.total_findings | Measure-Object -Sum).Sum
$coverage = [math]::Round(100 * $auditedRecords / $totalRecords, 2)
$findingRate = [math]::Round(100 * $totalFindings / $auditedRecords, 2)

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Production Audit Status')
$lines.Add('')
$lines.Add("Generated from ``ledger.jsonl``. Only completed adjudications contribute findings.")
$lines.Add('')
$lines.Add('| Measure | Value |')
$lines.Add('|---|---:|')
$lines.Add("| Corpus records | $totalRecords |")
$lines.Add("| Audited records | $auditedRecords |")
$lines.Add("| Coverage | $coverage% |")
$lines.Add("| Completed units | $($complete.Count) / $($entries.Count) |")
$lines.Add("| Adjudicated findings | $totalFindings |")
$lines.Add("| Findings per 100 audited records | $findingRate |")
$lines.Add('')
$lines.Add('## Book Coverage')
$lines.Add('')
$lines.Add('| Book | Audited | Total | Coverage | Findings |')
$lines.Add('|---:|---:|---:|---:|---:|')
foreach ($book in 1..24) {
    $bookEntries = @($entries | Where-Object book -eq $book)
    $bookComplete = @($bookEntries | Where-Object status -eq 'complete')
    $bookTotal = ($bookEntries.expected_record_count | Measure-Object -Sum).Sum
    $bookAudited = if ($bookComplete.Count) {
        ($bookComplete.expected_record_count | Measure-Object -Sum).Sum
    } else { 0 }
    $bookFindings = if ($bookComplete.Count) {
        ($bookComplete.metrics.total_findings | Measure-Object -Sum).Sum
    } else { 0 }
    $bookCoverage = [math]::Round(100 * $bookAudited / $bookTotal, 2)
    $lines.Add("| $book | $bookAudited | $bookTotal | $bookCoverage% | $bookFindings |")
}
$lines.Add('')
$lines.Add('## Next Batch')
$lines.Add('')
$next = $entries | Where-Object status -eq 'planned' | Select-Object -First 1
if ($next) {
    $lines.Add("``$($next.batch_id)``: *Odyssey* $($next.book).$($next.start_line)-$($next.end_line), $($next.expected_record_count) records.")
} else {
    $lines.Add('All planned batches are complete.')
}

$lines | Set-Content -LiteralPath $outputPath -Encoding utf8
Get-Item -LiteralPath $outputPath | Select-Object FullName, Length
