$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$background = Join-Path $root "assets\odyssey-living-manuscript-bg.png"
$audio = Join-Path $root "audio-chunks\book-01\chunk-001.mp3"
$cueDataPath = Join-Path $root "captions\book-01-preview-cues-v4.json"
$captions = Join-Path $root "captions\book-01-preview-v4.ass"
$output = Join-Path $root "videos\odyssey-book-01-preview-v4.mp4"

python (Join-Path $PSScriptRoot "make_preview_captions.py")

$captionFilterPath = $captions.Replace("\", "/").Replace(":", "\:")
$duration = [double]((Get-Content -Raw $cueDataPath | ConvertFrom-Json).duration)
$filter = "[0:v]scale=1920:1080,vignette=PI/5," +
          "subtitles=filename='$captionFilterPath'[video]"

ffmpeg -hide_banner -y `
    -loop 1 -framerate 30 -i $background `
    -i $audio `
    -t $duration `
    -filter_complex $filter `
    -map "[video]" -map "1:a:0" `
    -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 `
    -c:a aac -b:a 192k `
    -movflags +faststart `
    $output

if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg render failed with exit code $LASTEXITCODE"
}

Write-Host "Rendered $output"
