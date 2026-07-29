[CmdletBinding()]
param(
    [ValidateRange(1, 24)]
    [int]$Book = 1,

    [ValidateRange(1, 9999)]
    [int]$StartLine = 1,

    [ValidateRange(1, 9999)]
    [int]$EndLine = 155,

    [string]$SampleDirectory = (Join-Path $PSScriptRoot 'sample'),

    [string]$FormulaFileName = 'formulas-relevant.md'
)

$ErrorActionPreference = 'Stop'
if ($EndLine -lt $StartLine) {
    throw 'EndLine must be greater than or equal to StartLine.'
}

$auditRoot = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $auditRoot
$sampleDir = $SampleDirectory
New-Item -ItemType Directory -Path $sampleDir -Force | Out-Null

$bookNumber = '{0:D2}' -f $Book
$lineRange = '{0:D3}-{1:D3}' -f $StartLine, $EndLine
$greekRelativePath = "greek/book-$bookNumber.txt"
$translationRelativePath = "translation/book-$bookNumber.md"
$greekPath = Join-Path $root $greekRelativePath
$translationPath = Join-Path $root $translationRelativePath
$formulasPath = Join-Path $root 'FORMULAS.md'

$greek = Get-Content -LiteralPath $greekPath | Where-Object {
    if ($_ -match '^(\d+)\t') {
        $number = [int]$Matches[1]
        return $number -ge $StartLine -and $number -le $EndLine
    }
    return $false
}
Set-Content -LiteralPath (Join-Path $sampleDir "greek-book-$bookNumber-lines-$lineRange.txt") -Value $greek -Encoding utf8

$translation = Get-Content -LiteralPath $translationPath
$verseLines = $translation | Where-Object {
    if ($_ -match '^(\d+)\s{2}') {
        $number = [int]$Matches[1]
        return $number -ge $StartLine -and $number -le $EndLine
    }
    return $false
}
Set-Content -LiteralPath (Join-Path $sampleDir "translation-book-$bookNumber-lines-$lineRange.md") -Value $verseLines -Encoding utf8

$noteIds = [System.Collections.Generic.HashSet[string]]::new()
foreach ($line in $verseLines) {
    foreach ($match in [regex]::Matches($line, '\[\^([^\]]+)\]')) {
        [void]$noteIds.Add($match.Groups[1].Value)
    }
}
$notes = foreach ($line in $translation) {
    if ($line -match '^\[\^([^\]]+)\]:') {
        if ($noteIds.Contains($Matches[1])) { $line }
    }
}
Set-Content -LiteralPath (Join-Path $sampleDir "translation-notes-lines-$lineRange.md") -Value $notes -Encoding utf8

# The full register is small enough to include and avoids missing formulas whose
# first-use reference falls outside the sampled line range.
Copy-Item -LiteralPath $formulasPath -Destination (Join-Path $sampleDir $FormulaFileName) -Force

$sourcePaths = @(
    $greekRelativePath
    $translationRelativePath
    'FORMULAS.md'
)
$sourcePaths | ForEach-Object {
    $sourcePath = Join-Path $root $_
    [pscustomobject]@{
        RelativePath = $_
        Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
    }
} |
    ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $sampleDir 'source-hashes-before.json') -Encoding utf8
