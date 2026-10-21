# Development-only: build PyAV against an LGPL shared FFmpeg for Windows.
# The fetched bytes are recorded; this does NOT authorize a public release.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')))
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$wheelRoot = Join-Path (Get-Location) 'build\lgpl-wheel'
$archive = Join-Path $wheelRoot 'ffmpeg-lgpl.zip'
$assetUrl = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n9.0-latest-win64-lgpl-shared-9.0.zip'
New-Item -ItemType Directory -Force $wheelRoot | Out-Null
Write-Host 'Fetching LGPL shared FFmpeg. Development QA only; exact hash is recorded.'
Invoke-WebRequest -Uri $assetUrl -OutFile $archive -MaximumRedirection 8
$hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne '453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a') { throw 'Downloaded LGPL FFmpeg does not match pinned official release SHA-256' }
if ((Get-Item $archive).Length -lt 10000000) { throw 'FFmpeg archive unexpectedly small' }
$extract = Join-Path $wheelRoot 'lgpl-ffmpeg'
New-Item -ItemType Directory -Force $extract | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
$found = Get-ChildItem -Path $extract -Recurse -Filter ffmpeg.exe -File | Select-Object -First 1
if (-not $found) { throw 'LGPL FFmpeg executable not found in downloaded archive' }
$prefix = $found.Directory.Parent.FullName
$binaryDir = $found.Directory.FullName
if (-not (Test-Path (Join-Path $prefix 'include'))) { throw 'FFmpeg development headers missing' }
if (-not (Test-Path (Join-Path $prefix 'lib'))) { throw 'FFmpeg development import libraries missing' }
New-Item -ItemType Directory -Force 'bin' | Out-Null
Copy-Item -Path (Join-Path $binaryDir 'ffmpeg.exe') -Destination 'bin\ffmpeg.exe' -Force
Copy-Item -Path (Join-Path $binaryDir 'ffprobe.exe') -Destination 'bin\ffprobe.exe' -Force
Copy-Item -Path (Join-Path $binaryDir '*.dll') -Destination 'bin' -Force
$flags = & '.\bin\ffmpeg.exe' -version
if ($LASTEXITCODE -ne 0) { throw 'LGPL FFmpeg cannot run in Windows' }
$configuration = ($flags | Where-Object { $_ -match '^\s*configuration:' }) -join ' '
if (-not $configuration) { throw 'FFmpeg build does not disclose configuration' }
if ($configuration -match '--enable-(gpl|nonfree|libx264|libx265)(\s|$)') { throw 'GPL or nonfree FFmpeg was rejected' }
$encoders = & '.\bin\ffmpeg.exe' -hide_banner -encoders
if ($LASTEXITCODE -ne 0 -or ($encoders -join "`n") -notmatch 'libmp3lame' -or ($encoders -join "`n") -notmatch '(?m)^\s*A[\.A-Z\s]+aac\s') {
  throw 'Selected LGPL build lacks MP3/AAC export support; do not replace the existing app dependencies'
}
# Build from PyAV upstream source; never ship its default PyPI Windows wheel,
# which currently embeds GPL-enabled x264/x265 native libraries.
& $python -m pip install --upgrade 'Cython>=3,<4' 'wheel>=0.45' 'delvewheel>=1.9' 'setuptools>=80' 'packaging>=24'
if ($LASTEXITCODE -ne 0) { throw 'Unable to install PyAV build tools' }
$src = Join-Path $wheelRoot 'source'
New-Item -ItemType Directory -Force $src | Out-Null
& $python -m pip download --no-deps --no-binary av -d $src 'av==16.0.1'
if ($LASTEXITCODE -ne 0) { throw 'Could not download official PyAV 16.0.1 source archive' }
$tarFile = Get-ChildItem -Path $src -Filter 'av-16.0.1.tar.gz' | Select-Object -First 1
if (-not $tarFile) { throw 'PyAV 16.0.1 source missing' }
if ((Get-FileHash $tarFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf') { throw 'Official PyAV source digest has changed' }
# Windows ships tar.exe. The user-provided output folder is not used.
& tar.exe -xzf $tarFile.FullName -C $src
if ($LASTEXITCODE -ne 0) { throw 'Unable to extract PyAV source' }
$sourceDir = Join-Path $src 'av-16.0.1'
if (-not (Test-Path (Join-Path $sourceDir 'setup.py'))) { throw 'Official PyAV setup.py missing' }
Push-Location $sourceDir
try {
  & $python setup.py bdist_wheel "--ffmpeg-dir=$prefix"
  if ($LASTEXITCODE -ne 0) { throw 'PyAV LGPL source wheel build failed' }
  $built = Get-ChildItem -Path 'dist' -Filter 'av-16.0.1-*.whl' | Select-Object -First 1
  if (-not $built) { throw 'PyAV wheel not produced' }
  & $python -m delvewheel repair --add-path $binaryDir -w (Join-Path $wheelRoot 'repaired') $built.FullName
  if ($LASTEXITCODE -ne 0) { throw 'PyAV LGPL wheel DLL repair failed' }
} finally { Pop-Location }
$w = Get-ChildItem -Path (Join-Path $wheelRoot 'repaired') -Filter 'av-16.0.1-*.whl' | Select-Object -First 1
if (-not $w) { throw 'Repaired PyAV LGPL wheel missing' }
& $python -m pip uninstall -y av
if ($LASTEXITCODE -ne 0) { throw 'Uninstalling default GPL-linked PyAV failed' }
& $python -m pip install --no-deps --force-reinstall $w.FullName
if ($LASTEXITCODE -ne 0) { throw 'Installing LGPL-linked PyAV failed' }
$env:PATH = $binaryDir + ';' + $env:PATH
& $python -c 'from av import library_versions; from faster_whisper.audio import decode_audio; print("PyAV FFmpeg versions:",library_versions)'
if ($LASTEXITCODE -ne 0) { throw 'PyAV LGPL import/audio compatibility failed' }
& $python qa\validate_lgpl_media.py --directory bin --av-wheel $w.FullName
if ($LASTEXITCODE -ne 0) { throw 'LGPL compatibility validation failed' }
$receipt = @{
   source_url = $assetUrl
   ffmpeg_archive_sha256 = $hash
   ffmpeg_archive_bytes = (Get-Item $archive).Length
   pyav_source_sha256 = (Get-FileHash $tarFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
   repaired_pyav_wheel_sha256 = (Get-FileHash $w.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
   ffmpeg_configuration = $configuration
   release_allowed = $false
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $wheelRoot 'lgpl-media-receipt.json') -Encoding UTF8
Write-Host 'LGPL media build completed. Release stays blocked pending full legal review.'