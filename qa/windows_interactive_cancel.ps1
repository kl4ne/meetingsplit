# Windows disposable runner QA: drive Inno's real *interactive wizard* cancel path.
# No /VERYSILENT: WM_CLOSE and a scoped Yes response. Fail closed if GUI
# automation is not possible on this runner. Never run on a user's machine.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:GITHUB_REPOSITORY -ne 'kl4ne/meetingsplit') {
    throw 'Interactive installer test permitted only in isolated MeetingSplit GitHub Actions.'
}
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$root = Join-Path $repo 'work\interactive-cancel-qa'
$dest = Join-Path $root 'app'
$setup = Join-Path $repo 'dist\MeetingSplit_Setup_v0.8.6.exe'
New-Item -ItemType Directory -Force $root | Out-Null
if (-not (Test-Path -LiteralPath $setup)) { throw 'Exact pinned QA installer is unavailable' }
$log = Join-Path $root 'installer.log'
$report = Join-Path $root 'interactive-cancel.json'

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class MeetingSplitQaWindows {
    private delegate bool Enumerator(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] private static extern bool EnumWindows(Enumerator callback, IntPtr lParam);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int length);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    public static IntPtr[] VisibleWindows(uint expectedPid) {
        var found = new List<IntPtr>();
        EnumWindows((window, unused) => {
            uint pid;
            GetWindowThreadProcessId(window, out pid);
            if (pid == expectedPid && IsWindowVisible(window)) found.Add(window);
            return true;
        }, IntPtr.Zero);
        return found.ToArray();
    }
    public static string Title(IntPtr window) {
        var b = new StringBuilder(512);
        GetWindowText(window, b, b.Capacity);
        return b.ToString();
    }
}
'@

# Explicitly do NOT pass /SILENT or /VERYSILENT; this must test the wizard.
$arguments = @('/SP-', '/NORESTART', '/NOICONS', '/TASKS=""',
               ('/DIR="' + $dest + '"'), ('/LOG="' + $log + '"'))
$proc = Start-Process -FilePath $setup -ArgumentList $arguments -PassThru
$seenWindows = @()
$cancelSent = $false
$yesSent = $false
try {
    $readyDeadline = [Diagnostics.Stopwatch]::StartNew()
    while ($readyDeadline.Elapsed.TotalSeconds -lt 40) {
        $proc.Refresh()
        if ($proc.HasExited) { throw 'Setup exited before any interactive window was observed' }
        $visible = @([MeetingSplitQaWindows]::VisibleWindows([uint32]$proc.Id))
        if ($visible.Count -gt 0) {
            $seenWindows = @($visible | ForEach-Object { [MeetingSplitQaWindows]::Title($_) })
            # Cancel at wizard stage BEFORE any actual file copy or app launch.
            foreach ($h in $visible) {
                [void][MeetingSplitQaWindows]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
            }
            $cancelSent = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $cancelSent) { throw 'Interactive Windows desktop not available: cancellation unverified' }

    $cancelDeadline = [Diagnostics.Stopwatch]::StartNew()
    while ($cancelDeadline.Elapsed.TotalSeconds -lt 30) {
        $proc.Refresh()
        if ($proc.HasExited) { break }
        foreach ($h in [MeetingSplitQaWindows]::VisibleWindows([uint32]$proc.Id)) {
            # IDYES=6 for native Windows confirmation dialogs. Only this
            # process's own windows receive WM_COMMAND, not any other app.
            [void][MeetingSplitQaWindows]::PostMessage($h, 0x0111, [IntPtr]6, [IntPtr]::Zero)
            $yesSent = $true
        }
        Start-Sleep -Milliseconds 250
    }
    $proc.Refresh()
    if (-not $proc.HasExited) { throw 'Installer did not exit after window-close and confirmation request' }
    if (Test-Path -LiteralPath (Join-Path $dest 'MeetingSplit.exe')) {
        throw 'Installer cancellation unexpectedly left an installed app'
    }
    @{
        version = '0.8.6'
        interactive_window_seen = $true
        window_titles = $seenWindows
        wm_close_sent = $cancelSent
        confirmation_attempted = $yesSent
        installer_exited = $true
        no_installed_app = $true
        test_scope = 'wizard cancellation before files were copied; NOT mid-install cancellation'
        installer_exit_code = $proc.ExitCode
        public_release_allowed = $false
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $report -Encoding UTF8
    Write-Host 'Isolated interactive setup wizard cancellation QA passed. Mid-copy cancellation still unverified.'
} finally {
    $proc.Refresh()
    if (-not $proc.HasExited) {
        & "$env:SystemRoot\System32\taskkill.exe" /PID $proc.Id /T /F 2>$null | Out-Null
    }
}
