[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$auditRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $auditRoot
$ledgerPath = Join-Path $auditRoot 'ledger.jsonl'
$rubricPath = Join-Path $auditRoot 'rubric.md'
$calibrationPath = Join-Path $auditRoot 'reviewer-calibration.md'
if (Test-Path -LiteralPath $ledgerPath) {
    throw "Ledger already exists at '$ledgerPath'. Initialization is creation-only."
}

$ranges = [ordered]@{
    1 = @('1-155', '156-444')
    2 = @('1-217', '218-434')
    3 = @('1-248', '249-497')
    4 = @('1-211', '212-423', '424-635', '636-847')
    5 = @('1-246', '247-493')
    6 = @('1-165', '166-331')
    7 = @('1-173', '174-347')
    8 = @('1-195', '196-390', '391-586')
    9 = @('1-172', '173-344', '345-566')
    10 = @('1-191', '192-382', '383-574')
    11 = @('1-213', '214-426', '427-640')
    12 = @('1-226', '227-453')
    13 = @('1-220', '221-440')
    14 = @('1-177', '178-355', '356-533')
    15 = @('1-185', '186-371', '372-557')
    16 = @('1-240', '241-481')
    17 = @('1-202', '203-404', '405-606')
    18 = @('1-214', '215-428')
    19 = @('1-201', '202-402', '403-604')
    20 = @('1-197', '198-394')
    21 = @('1-217', '218-434')
    22 = @('1-167', '168-334', '335-501')
    23 = @('1-186', '187-372')
    24 = @('1-182', '183-365', '366-548')
}

$completed = @{
    'odyssey-01-001-155' = [pscustomobject]@{
        Directory = 'audit-poc'
        Critical = 0; Major = 0; Moderate = 3; Minor = 0
        Total = 3; Rate = 1.94; Jaccard = 75.0
    }
    'odyssey-09-345-566' = [pscustomobject]@{
        Directory = 'audit-pilot-book09'
        Critical = 0; Major = 0; Moderate = 1; Minor = 3
        Total = 4; Rate = 1.80; Jaccard = 0.0
    }
}

$rubricHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $rubricPath).Hash
$calibrationHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $calibrationPath).Hash
$records = [System.Collections.Generic.List[object]]::new()

foreach ($bookEntry in $ranges.GetEnumerator()) {
    $book = [int]$bookEntry.Key
    $bookNumber = '{0:D2}' -f $book
    $greekRelative = "greek/book-$bookNumber.txt"
    $translationRelative = "translation/book-$bookNumber.md"
    $greekPath = Join-Path $repoRoot $greekRelative
    $translationPath = Join-Path $repoRoot $translationRelative
    $assignedLabels = [System.Collections.Generic.HashSet[int]]::new()

    $greekLabels = @(Get-Content -LiteralPath $greekPath | ForEach-Object {
        if ($_ -match '^(\d+)\t') { [int]$Matches[1] }
    })
    $translationLabels = @(Get-Content -LiteralPath $translationPath | ForEach-Object {
        if ($_ -match '^(\d+)\s{2}') { [int]$Matches[1] }
    })
    if (($greekLabels -join ',') -ne ($translationLabels -join ',')) {
        throw "Greek and English line labels differ for Book $book."
    }

    foreach ($range in $bookEntry.Value) {
        $parts = $range -split '-'
        $startLine = [int]$parts[0]
        $endLine = [int]$parts[1]
        $batchId = 'odyssey-{0:D2}-{1:D3}-{2:D3}' -f $book, $startLine, $endLine
        $selectedLabels = @($greekLabels | Where-Object { $_ -ge $startLine -and $_ -le $endLine })
        if ($selectedLabels.Count -eq 0) {
            throw "Batch '$batchId' contains no source records."
        }
        foreach ($label in $selectedLabels) {
            if (-not $assignedLabels.Add($label)) {
                throw "Book $book line $label is assigned to more than one batch."
            }
        }
        $absentLabels = @($startLine..$endLine | Where-Object { $_ -notin $selectedLabels })
        $isComplete = $completed.ContainsKey($batchId)
        $prior = if ($isComplete) { $completed[$batchId] } else { $null }
        $batchDirectory = if ($isComplete) {
            $prior.Directory
        } else {
            "audit-production/batches/$batchId"
        }

        $records.Add([ordered]@{
            schema_version = 1
            batch_id = $batchId
            book = $book
            start_line = $startLine
            end_line = $endLine
            expected_record_count = $selectedLabels.Count
            absent_labels = $absentLabels
            status = if ($isComplete) { 'complete' } else { 'planned' }
            calibration_version = if ($isComplete) { 'pilot-v0' } else { 'semantic-only-formula-automation-v1' }
            rubric_sha256 = if ($isComplete) { $null } else { $rubricHash }
            calibration_sha256 = if ($isComplete) { $null } else { $calibrationHash }
            incorporated_into_calibration_version = if ($isComplete) { 'book01-book09-v1' } else { $null }
            sources = [ordered]@{
                greek_path = $greekRelative
                greek_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $greekPath).Hash
                translation_path = $translationRelative
                translation_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $translationPath).Hash
                formula_path = 'FORMULAS.md'
                formula_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot 'FORMULAS.md')).Hash
            }
            artifacts = [ordered]@{
                batch_directory = $batchDirectory
                manifest = if ($isComplete) { $null } else { "$batchDirectory/manifest.json" }
                reviewer_1 = "$batchDirectory/reviews/reviewer-1.md"
                reviewer_2 = "$batchDirectory/reviews/reviewer-2.md"
                adjudication = "$batchDirectory/reviews/adjudication.md"
                adjudication_result = if ($isComplete) { $null } else { "$batchDirectory/reviews/adjudication-result.json" }
                report = "$batchDirectory/report.md"
            }
            integrity = [ordered]@{
                manifest_sha256 = $null
                reviewer_1_sha256 = $null
                reviewer_2_sha256 = $null
                adjudication_sha256 = $null
                adjudication_result_sha256 = $null
                report_sha256 = $null
            }
            review = [ordered]@{
                reviewer_1_status = if ($isComplete) { 'complete' } else { 'pending' }
                reviewer_2_status = if ($isComplete) { 'complete' } else { 'pending' }
                adjudication_status = if ($isComplete) { 'complete' } else { 'pending' }
            }
            metrics = [ordered]@{
                critical = if ($isComplete) { $prior.Critical } else { $null }
                major = if ($isComplete) { $prior.Major } else { $null }
                moderate = if ($isComplete) { $prior.Moderate } else { $null }
                minor = if ($isComplete) { $prior.Minor } else { $null }
                total_findings = if ($isComplete) { $prior.Total } else { $null }
                findings_per_100 = if ($isComplete) { $prior.Rate } else { $null }
                reviewer_jaccard = if ($isComplete) { $prior.Jaccard } else { $null }
            }
        })
    }
    if (($assignedLabels.Count -ne $greekLabels.Count) -or
        (($assignedLabels | Sort-Object) -join ',') -ne (($greekLabels | Sort-Object) -join ',')) {
        throw "Batch ranges do not cover every Book $book source record exactly once."
    }
}

$temporaryLedger = "$ledgerPath.tmp"
$records | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress } |
    Set-Content -LiteralPath $temporaryLedger -Encoding utf8
Get-Content -LiteralPath $temporaryLedger | ForEach-Object { $null = $_ | ConvertFrom-Json }
Move-Item -LiteralPath $temporaryLedger -Destination $ledgerPath -Force

$summary = [pscustomobject]@{
    Units = $records.Count
    Complete = @($records | Where-Object status -eq 'complete').Count
    Planned = @($records | Where-Object status -eq 'planned').Count
    TotalRecords = ($records.expected_record_count | Measure-Object -Sum).Sum
    AuditedRecords = (($records | Where-Object status -eq 'complete').expected_record_count | Measure-Object -Sum).Sum
}
$summary | Format-Table -AutoSize
