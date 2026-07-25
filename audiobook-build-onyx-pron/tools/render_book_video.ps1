param(
    [string]$Book = "book-01",
    [switch]$SkipCaptions
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python312 = "C:\Users\executor\.pyenv\pyenv-win\versions\3.12.10\python.exe"
$background = Join-Path $root "assets\odyssey-living-manuscript-bg.png"
$audio = Join-Path $root "books\$Book.mp3"
$captions = Join-Path $root "captions\$Book.ass"
$cueDataPath = Join-Path $root "captions\$Book-cues.json"
$output = Join-Path $root "videos\odyssey-$Book-full.mp4"

if (-not $SkipCaptions) {
    & $python312 (Join-Path $PSScriptRoot "build_book_captions.py") --book $Book
    if ($LASTEXITCODE -ne 0) {
        throw "Caption generation failed with exit code $LASTEXITCODE"
    }
}

$duration = [double]((Get-Content -Raw $cueDataPath | ConvertFrom-Json).duration)
$captionFilterPath = $captions.Replace("\", "/").Replace(":", "\:")
$filter = "[0:v]scale=1920:1080,vignette=PI/5," +
          "subtitles=filename='$captionFilterPath'[video]"

ffmpeg -hide_banner -y `
    -loop 1 -framerate 24 -i $background `
    -i $audio `
    -t $duration `
    -filter_complex $filter `
    -map "[video]" -map "1:a:0" `
    -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r 24 `
    -c:a aac -b:a 128k `
    -movflags +faststart `
    $output

if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg render failed with exit code $LASTEXITCODE"
}

Write-Host "Rendered $output"
