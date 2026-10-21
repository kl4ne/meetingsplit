# Run ONLY on an ephemeral GitHub Windows runner. Never overwrite a user's app.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Installer smoke test is restricted to disposable CI runners.' }
$repoTask = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$setupTask = Join-Path $repoTask 'dist\MeetingSplit_Setup_v0.8.6.exe'
$qaRootTask = Join-Path $repoTask 'work\installer-smoke'
$installTask = Join-Path $qaRootTask 'app'
$dataTask = Join-Path $qaRootTask 'data'
New-Item -ItemType Directory -Force $qaRootTask,$dataTask | Out-Null
Set-Content -LiteralPath (Join-Path $dataTask 'preserve.txt') -Value 'Synthetic data must survive uninstall.'

function Invoke-BoundedInstallerTask([string]$exeTask, [string[]]$argsTask) {
    $processTask = Start-Process -FilePath $exeTask -ArgumentList $argsTask -PassThru -WindowStyle Hidden
    if (-not $processTask.WaitForExit(180000)) {
        Stop-Process -Id $processTask.Id -Force
        throw 'Installer QA process timed out in 180 seconds.'
    }
    if ($processTask.ExitCode -ne 0) { throw "Installer QA exited with $($processTask.ExitCode)" }
}

$argsTask = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/TASKS=""',
    ('/DIR="'+$installTask+'"'),('/LOG="'+(Join-Path $qaRootTask 'install.log')+'"'))
Invoke-BoundedInstallerTask $setupTask $argsTask
$exeTask = Join-Path $installTask 'MeetingSplit.exe'
if (-not (Test-Path -LiteralPath $exeTask)) { throw 'Clean install did not create the app.' }
if (-not (Test-Path -LiteralPath (Join-Path $installTask '_internal\docs\OPTIONAL_COMPONENTS.md'))) { throw 'Component/license notices missing.' }
Invoke-BoundedInstallerTask $exeTask @('--self-check',('"'+(Join-Path $qaRootTask 'frozen-check.json')+'"'))
$checkTask = Get-Content -LiteralPath (Join-Path $qaRootTask 'frozen-check.json') -Raw | ConvertFrom-Json
if (-not $checkTask.packaged) { throw 'Self-check did not run from frozen application.' }
$env:QT_QPA_PLATFORM = 'offscreen'
$env:QTWEBENGINE_CHROMIUM_FLAGS = '--disable-gpu'
$uiReportTask = Join-Path $qaRootTask 'frozen-ui-check.json'
Invoke-BoundedInstallerTask $exeTask @('--ui-qa',('"'+$uiReportTask+'"'))
$uiCheckTask = Get-Content -LiteralPath $uiReportTask -Raw | ConvertFrom-Json
if (-not $uiCheckTask.ok) { throw 'Frozen WebEngine did not render the existing five-screen UI.' }

# Upgrade/reinstall over the test installation; no real user installation exists.
Invoke-BoundedInstallerTask $setupTask $argsTask
if (-not (Test-Path -LiteralPath $exeTask)) { throw 'Reinstall lost the app.' }
Invoke-BoundedInstallerTask (Join-Path $installTask 'unins000.exe') @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
if (Test-Path -LiteralPath $exeTask) { throw 'Uninstall did not remove the executable.' }
if (-not (Test-Path -LiteralPath (Join-Path $dataTask 'preserve.txt'))) { throw 'Uninstall removed data outside app folder.' }

@{
    clean_install = $true; same_version_reinstall = $true; uninstall = $true
    external_data_preserved = $true; frozen_self_check = $checkTask; frozen_ui = $uiCheckTask
    not_tested = @('interactive cancellation','upgrade from user-installed 0.8.5',
        'optional runtime network installation','GPU inference on runner','SmartScreen/signing')
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $qaRootTask 'installer-qa.json') -Encoding UTF8
Write-Output 'Disposable Windows installer smoke checks passed.'
