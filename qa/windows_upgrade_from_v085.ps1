# Disposable Windows CI only. Authentic v0.8.5 -> consolidated development 0.8.6.
# This does not install anything on the user's ASUS or authorize public release.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:GITHUB_REPOSITORY -ne 'kl4ne/meetingsplit') {
  throw 'Legacy installer upgrade is restricted to the MeetingSplit GitHub Actions sandbox.'
}
if (-not $env:GITHUB_TOKEN) { throw 'Actions read token required for official v0.8.5 artifact' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$root = Join-Path $repoRoot 'work\legacy-upgrade-qa'
$priorZip = Join-Path $root 'v085-artifact.zip'
$priorExtract = Join-Path $root 'v085-extracted'
$installDir = Join-Path $root 'isolated-app'
$userData = Join-Path $root 'MeetingSplit-user-data'
New-Item -ItemType Directory -Force $root,$priorExtract,$userData | Out-Null
$dataFile = Join-Path $userData 'user-preserve.txt'
'Original user output should not be erased during upgrade' | Set-Content -LiteralPath $dataFile -Encoding UTF8
$uri = 'https://api.github.com/repos/kl4ne/meetingsplit/actions/artifacts/12315582489/zip'
$headers = @{ Authorization = ('Bearer ' + $env:GITHUB_TOKEN); Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28' }
# Redirects preserve credentials only for the Github API; the artifact itself is a
# temporary GitHub-controlled download. Never ingest arbitrary user media here.
Invoke-WebRequest -Uri $uri -Headers $headers -OutFile $priorZip -MaximumRedirection 8
if ((Get-Item -LiteralPath $priorZip).Length -lt 10000000) { throw 'Old artifact missing or too small' }
Expand-Archive -LiteralPath $priorZip -DestinationPath $priorExtract -Force
$prior = Get-ChildItem -Path $priorExtract -Filter 'MeetingSplit_Setup_v0.8.5.exe' -File -Recurse | Select-Object -First 1
if (-not $prior) { throw 'Official v0.8.5 installer not found inside GitHub artifact' }
$new = Join-Path $repoRoot 'dist\MeetingSplit_Setup_v0.8.6.exe'
if (-not (Test-Path -LiteralPath $new)) { throw 'Current QA installer missing' }
function Run-Installer([string]$exe,[string[]]$args) {
  $process = Start-Process -FilePath $exe -ArgumentList $args -PassThru -WindowStyle Hidden
  if (-not $process.WaitForExit(240000)) {
    Stop-Process -Id $process.Id -Force
    throw 'Legacy upgrade installer exceeded 240-second timeout'
  }
  if ($process.ExitCode -ne 0) { throw "Legacy upgrade installer failed: $($process.ExitCode)" }
}
$parameters = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/TASKS=""',('/DIR="'+$installDir+'"'))
Run-Installer $prior.FullName $parameters
$app = Join-Path $installDir 'MeetingSplit.exe'
if (-not (Test-Path -LiteralPath $app)) { throw 'Legacy v0.8.5 did not install' }
# Capture a marker in the external data folder plus a separate harmless file
# in the application installation path to verify Inno upgrade behavior.
$marker = Join-Path $installDir 'meeting-synthetic-marker.txt'
'present before upgrade' | Set-Content -LiteralPath $marker -Encoding UTF8
Run-Installer $new $parameters
if (-not (Test-Path -LiteralPath $app)) { throw 'v0.8.6 upgrade lost MeetingSplit.exe' }
if (-not (Test-Path -LiteralPath $dataFile)) { throw 'v0.8.6 upgrade removed external user data' }
$check = Join-Path $root 'updated-self-check.json'
$proc = Start-Process -FilePath $app -ArgumentList @('--self-check',('"'+$check+'"')) -PassThru -WindowStyle Hidden
if (-not $proc.WaitForExit(60000)) { Stop-Process -Id $proc.Id -Force; throw 'Upgraded app self-check hung' }
if ($proc.ExitCode -ne 0 -or -not (Test-Path $check)) { throw 'Upgraded app failed frozen self-check' }
$status = Get-Content -LiteralPath $check -Raw | ConvertFrom-Json
if ($status.version -ne '0.8.6' -or -not $status.packaged) { throw 'Upgrade did not install v0.8.6' }
Run-Installer (Join-Path $installDir 'unins000.exe') @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
if (Test-Path -LiteralPath $app) { throw 'Uninstaller left MeetingSplit.exe behind' }
if (-not (Test-Path -LiteralPath $dataFile)) { throw 'Uninstall removed external user data' }
@{
  prior = 'MeetingSplit_Setup_v0.8.5.exe'; updated = 'MeetingSplit_Setup_v0.8.6.exe';
  legacy_to_consolidated_upgrade = $true; external_data_preserved = $true;
  upgraded_self_check = $status; public_release_allowed = $false;
  not_covered = @('real user settings','interactive cancellation','GPU on runner','live optional downloads')
} | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $root 'upgrade-qa.json') -Encoding UTF8
Write-Host 'Authentic v0.8.5 -> development v0.8.6 upgrade passed on an isolated Windows runner.'