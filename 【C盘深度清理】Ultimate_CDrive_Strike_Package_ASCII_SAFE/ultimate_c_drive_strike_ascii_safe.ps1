#requires -version 5.1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TimeTag   = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile   = Join-Path $ScriptDir "ultimate_strike_$TimeTag.log"
$TxtFile   = Join-Path $ScriptDir "ultimate_strike_report_$TimeTag.txt"
$JsonFile  = Join-Path $ScriptDir "ultimate_strike_report_$TimeTag.json"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level, $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Ensure-Admin {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($current)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
        $arg = '-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $PSCommandPath
        Start-Process powershell -Verb RunAs -ArgumentList $arg
        exit
    }
}

function Get-SizeString {
    param([double]$Bytes)
    if ($Bytes -ge 1TB) { return "{0:N2} TB" -f ($Bytes / 1TB) }
    elseif ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    elseif ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    elseif ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    else { return "{0} B" -f [int64]$Bytes }
}

function Get-CDriveState {
    $d = Get-PSDrive C
    [pscustomobject]@{
        UsedBytes = [double]$d.Used
        FreeBytes = [double]$d.Free
        TotalBytes = [double]($d.Used + $d.Free)
        UsedGB = [math]::Round($d.Used / 1GB, 2)
        FreeGB = [math]::Round($d.Free / 1GB, 2)
        TotalGB = [math]::Round(($d.Used + $d.Free) / 1GB, 2)
        UsedPct = if (($d.Used + $d.Free) -gt 0) { [math]::Round(($d.Used / ($d.Used + $d.Free)) * 100, 2) } else { 0 }
    }
}

function Read-YesNo {
    param([string]$Prompt, [bool]$Default = $true)
    $suffix = if ($Default) { " [Y/n]" } else { " [y/N]" }
    $ans = Read-Host ($Prompt + $suffix)
    if ([string]::IsNullOrWhiteSpace($ans)) { return $Default }
    return $ans -match '^[Yy]'
}

function Get-TreeSize {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path)) { return 0 }
    try {
        $sum = Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum
        return [double]($sum.Sum)
    } catch {
        return 0
    }
}

function Clear-DirectoryContents {
    param([string]$Path)
    $freed = 0
    if (!(Test-Path -LiteralPath $Path)) { return 0 }

    try {
        Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $size = 0
            try { $size = [double]$_.Length } catch {}
            try {
                Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
                if (!(Test-Path -LiteralPath $_.FullName)) { $freed += $size }
            } catch {}
        }
        Get-ChildItem -LiteralPath $Path -Force -Recurse -Directory -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            ForEach-Object {
                try { Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction SilentlyContinue } catch {}
            }
    } catch {}
    return $freed
}

function Add-ReportAction {
    param([string]$Name, [double]$Bytes, [string]$Note = "")
    $script:Actions += [pscustomobject]@{
        Name = $Name
        FreedBytes = [double]$Bytes
        Freed = Get-SizeString $Bytes
        Note = $Note
    }
}

function Analyze-CDrive {
    Write-Log "Starting deep analysis of drive C"
    $items = @()

    $criticalFiles = @(
        @{Name="pagefile.sys"; Path="C:\pagefile.sys"; Type="Critical File"; Suggest="Do not delete directly; reduce or move virtual memory."},
        @{Name="hiberfil.sys"; Path="C:\hiberfil.sys"; Type="Critical File"; Suggest="Can be removed by turning hibernation off."},
        @{Name="swapfile.sys"; Path="C:\swapfile.sys"; Type="Critical File"; Suggest="System file; do not delete manually."}
    )
    foreach ($x in $criticalFiles) {
        if (Test-Path -LiteralPath $x.Path) {
            $bytes = (Get-Item -LiteralPath $x.Path -Force).Length
            $items += [pscustomobject]@{
                Name=$x.Name; Path=$x.Path; Bytes=[double]$bytes; Size=(Get-SizeString $bytes); Type=$x.Type; Suggest=$x.Suggest
            }
        }
    }

    $majorDirs = @(
        @{Name="Windows"; Path="C:\Windows"; Type="System Folder"; Suggest="Do not delete manually; inspect WinSxS and Installer."},
        @{Name="Users"; Path="C:\Users"; Type="User Folder"; Suggest="Inspect AppData, Downloads, Desktop."},
        @{Name="Program Files"; Path="C:\Program Files"; Type="App Folder"; Suggest="Uninstall large apps you do not need."},
        @{Name="Program Files (x86)"; Path="C:\Program Files (x86)"; Type="App Folder"; Suggest="Uninstall large apps you do not need."},
        @{Name="ProgramData"; Path="C:\ProgramData"; Type="Hidden Folder"; Suggest="Inspect Package Cache and app caches."}
    )
    foreach ($x in $majorDirs) {
        if (Test-Path -LiteralPath $x.Path) {
            $bytes = Get-TreeSize $x.Path
            $items += [pscustomobject]@{
                Name=$x.Name; Path=$x.Path; Bytes=[double]$bytes; Size=(Get-SizeString $bytes); Type=$x.Type; Suggest=$x.Suggest
            }
        }
    }

    $focusDirs = @(
        @{Name="Windows\WinSxS"; Path="C:\Windows\WinSxS"; Type="System Component"; Suggest="Use DISM only; never delete manually."},
        @{Name="Windows\Installer"; Path="C:\Windows\Installer"; Type="Installer Cache"; Suggest="Do not delete manually."},
        @{Name="Users\Admin\AppData\Local"; Path="C:\Users\Administrator\AppData\Local"; Type="User Cache"; Suggest="Inspect Programs, JianyingPro, Google, Microsoft, pip, Doubao, Quark."},
        @{Name="Users\Admin\AppData\Local\Packages"; Path="C:\Users\Administrator\AppData\Local\Packages"; Type="UWP Cache"; Suggest="Inspect large child folders; do not wipe the whole folder blindly."},
        @{Name="Users\Admin\Downloads"; Path="C:\Users\Administrator\Downloads"; Type="Personal Files"; Suggest="Delete only what you recognize."},
        @{Name="Users\Admin\Desktop"; Path="C:\Users\Administrator\Desktop"; Type="Personal Files"; Suggest="Delete only what you recognize."},
        @{Name="ProgramData\Package Cache"; Path="C:\ProgramData\Package Cache"; Type="Installer Cache"; Suggest="May be removable after confirmation."},
        @{Name="ProgramData\Microsoft"; Path="C:\ProgramData\Microsoft"; Type="Hidden Folder"; Suggest="Inspect large child folders."},
        @{Name="Program Files\WindowsApps"; Path="C:\Program Files\WindowsApps"; Type="Store Apps"; Suggest="Uninstall through Windows settings, not by deleting files."},
        @{Name="Program Files\Microsoft Office"; Path="C:\Program Files\Microsoft Office"; Type="Large App"; Suggest="Uninstall if not needed."},
        @{Name="Program Files (x86)\Microsoft Visual Studio"; Path="C:\Program Files (x86)\Microsoft Visual Studio"; Type="Large App"; Suggest="Uninstall if not needed."},
        @{Name="Program Files (x86)\Windows Kits"; Path="C:\Program Files (x86)\Windows Kits"; Type="Dev Component"; Suggest="Uninstall if not needed."}
    )
    foreach ($x in $focusDirs) {
        if (Test-Path -LiteralPath $x.Path) {
            $bytes = Get-TreeSize $x.Path
            $items += [pscustomobject]@{
                Name=$x.Name; Path=$x.Path; Bytes=[double]$bytes; Size=(Get-SizeString $bytes); Type=$x.Type; Suggest=$x.Suggest
            }
        }
    }

    $breakdownParents = @(
        "C:\Users\Administrator\AppData\Local",
        "C:\ProgramData",
        "C:\Program Files",
        "C:\Program Files (x86)",
        "C:\Windows"
    )
    foreach ($parent in $breakdownParents) {
        if (Test-Path -LiteralPath $parent) {
            try {
                Get-ChildItem -LiteralPath $parent -Force -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                    $bytes = Get-TreeSize $_.FullName
                    $items += [pscustomobject]@{
                        Name=("Child: " + $_.Name)
                        Path=$_.FullName
                        Bytes=[double]$bytes
                        Size=(Get-SizeString $bytes)
                        Type="First Level Child"
                        Suggest=("Inside " + $parent)
                    }
                }
            } catch {}
        }
    }

    $script:TopItems = $items | Sort-Object Bytes -Descending | Select-Object -First 80
    Write-Log "Deep analysis completed"
}

function Export-Reports {
    $state = Get-CDriveState
    $report = [pscustomobject]@{
        GeneratedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Drive = $state
        Actions = $script:Actions
        TopItems = $script:TopItems
    }
    $report | ConvertTo-Json -Depth 6 | Out-File -FilePath $JsonFile -Encoding utf8

    $lines = @()
    $lines += "Ultimate C Drive Strike Report"
    $lines += "================================================================"
    $lines += "Generated At: $($report.GeneratedAt)"
    $lines += "Drive C: Used $($state.UsedGB) GB / Free $($state.FreeGB) GB / Total $($state.TotalGB) GB / Usage $($state.UsedPct)%"
    $lines += ""
    $lines += "Actions:"
    $i = 1
    foreach ($a in $script:Actions) {
        $lines += ("{0,2}. {1} -> {2}  {3}" -f $i, $a.Name, $a.Freed, $a.Note)
        $i++
    }
    $lines += ""
    $lines += "Top Usage Items:"
    $i = 1
    foreach ($x in $script:TopItems) {
        $lines += ("{0,2}. {1,-12} | {2} | {3} | {4}" -f $i, $x.Size, $x.Type, $x.Path, $x.Suggest)
        $i++
    }
    $lines | Out-File -FilePath $TxtFile -Encoding utf8

    Write-Log "TXT report exported: $TxtFile"
    Write-Log "JSON report exported: $JsonFile"
}

function Invoke-SafeAndAggressiveCleanup {
    Write-Log "Starting safe + aggressive cache cleanup"
    $before = Get-CDriveState

    $targets = @(
        @{Name="User Temp"; Path=$env:TEMP},
        @{Name="Windows Temp"; Path="C:\Windows\Temp"},
        @{Name="Recent"; Path=(Join-Path $env:USERPROFILE "Recent")},
        @{Name="CrashDumps"; Path=(Join-Path $env:LOCALAPPDATA "CrashDumps")},
        @{Name="Chrome Cache"; Path=(Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data\Default\Cache")},
        @{Name="Chrome Code Cache"; Path=(Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data\Default\Code Cache")},
        @{Name="Edge Cache"; Path=(Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data\Default\Cache")},
        @{Name="Edge Code Cache"; Path=(Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data\Default\Code Cache")},
        @{Name="Jianying Cache"; Path=(Join-Path $env:LOCALAPPDATA "JianyingPro\User Data\Cache")},
        @{Name="WER"; Path="C:\ProgramData\Microsoft\Windows\WER"},
        @{Name="Windows Update Download Cache"; Path="C:\Windows\SoftwareDistribution\Download"}
    )

    foreach ($t in $targets) {
        if ($t.Name -eq "Windows Update Download Cache") {
            try { net stop wuauserv | Out-Null } catch {}
            Start-Sleep -Seconds 2
            $freed = Clear-DirectoryContents $t.Path
            try { net start wuauserv | Out-Null } catch {}
        } else {
            $freed = Clear-DirectoryContents $t.Path
        }
        Add-ReportAction $t.Name $freed ""
        Write-Log ("{0} -> {1}" -f $t.Name, (Get-SizeString $freed))
    }

    $rb = 0
    try {
        $rb = [double]((Get-ChildItem 'C:\$Recycle.Bin' -Force -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)
        Clear-RecycleBin -Force -ErrorAction SilentlyContinue | Out-Null
    } catch {}
    Add-ReportAction "Recycle Bin" $rb ""
    Write-Log ("Recycle Bin -> {0}" -f (Get-SizeString $rb))

    $cacheNames = @("Cache","Code Cache","GPUCache","GrShaderCache","ShaderCache","DawnCache","Media Cache","Temp","tmp","CrashDumps")
    $roots = @(
        $env:LOCALAPPDATA,
        (Join-Path $env:USERPROFILE "AppData\LocalLow"),
        $env:APPDATA
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    foreach ($root in $roots) {
        Write-Log "Scanning deep cache folders under: $root"
        try {
            Get-ChildItem -LiteralPath $root -Force -Recurse -Directory -ErrorAction SilentlyContinue |
                Where-Object { $cacheNames -contains $_.Name } |
                Select-Object -Unique FullName, Name |
                ForEach-Object {
                    $freed = Clear-DirectoryContents $_.FullName
                    if ($freed -gt 0) {
                        Add-ReportAction ("Deep Cache: " + $_.FullName) $freed ""
                        Write-Log ("Deep Cache -> {0} | {1}" -f $_.FullName, (Get-SizeString $freed))
                    }
                }
        } catch {}
    }

    $pipFreed = 0
    $pipDir = Join-Path $env:LOCALAPPDATA "pip\Cache"
    if (Test-Path -LiteralPath $pipDir) {
        $beforePip = Get-TreeSize $pipDir
        try {
            python -m pip cache purge | Out-Null
        } catch {}
        Start-Sleep -Seconds 1
        $afterPip = Get-TreeSize $pipDir
        $pipFreed = [math]::Max(0, $beforePip - $afterPip)
        Add-ReportAction "pip cache purge" $pipFreed ""
        Write-Log ("pip cache purge -> {0}" -f (Get-SizeString $pipFreed))
    }

    $after = Get-CDriveState
    $delta = [math]::Max(0, [double]($after.FreeBytes - $before.FreeBytes))
    Add-ReportAction "Actual free space gained this round" $delta "Use actual disk delta as the source of truth."
    Write-Log ("Actual free space gained this round: {0}" -f (Get-SizeString $delta))
}

function Disable-Hibernation {
    $path = "C:\hiberfil.sys"
    $size = 0
    if (Test-Path $path) {
        $size = [double](Get-Item $path -Force).Length
    }
    try { powercfg -h off | Out-Null } catch {}
    Add-ReportAction "Disable hibernation" $size "If hibernation was already off, this may be 0 B."
    Write-Log ("Disable hibernation -> {0}" -f (Get-SizeString $size))
}

function Invoke-DismCleanup {
    $before = Get-CDriveState
    Write-Log "Starting DISM component cleanup"
    try {
        DISM /Online /Cleanup-Image /StartComponentCleanup | Tee-Object -FilePath $LogFile -Append
    } catch {}
    $after = Get-CDriveState
    $delta = [math]::Max(0, [double]($after.FreeBytes - $before.FreeBytes))
    Add-ReportAction "DISM component cleanup" $delta "Actual release amount is measured by disk delta."
    Write-Log ("DISM component cleanup -> {0}" -f (Get-SizeString $delta))
}

function Open-UninstallCenter {
    Write-Log "Opening uninstall center"
    Start-Process "appwiz.cpl"
}

function Open-PagefileSettings {
    Write-Log "Opening performance settings"
    Start-Process "SystemPropertiesPerformance.exe"
}

function Show-MenuHeader {
    Clear-Host
    $state = Get-CDriveState
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "               Ultimate C Drive Strike (ASCII)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ("Drive C: Used {0} GB / Free {1} GB / Total {2} GB / Usage {3}%" -f $state.UsedGB, $state.FreeGB, $state.TotalGB, $state.UsedPct) -ForegroundColor Green
    Write-Host ""
    if ($script:TopItems -and $script:TopItems.Count -gt 0) {
        Write-Host "Top 15 current usage items:" -ForegroundColor Cyan
        $i = 1
        foreach ($x in ($script:TopItems | Select-Object -First 15)) {
            Write-Host ("{0,2}. {1,-12} | {2}" -f $i, $x.Size, $x.Path)
            $i++
        }
        Write-Host ""
    }
}

function Invoke-UltimateStrike {
    Write-Log "Starting full strike sequence"
    Analyze-CDrive
    Invoke-SafeAndAggressiveCleanup
    if (Read-YesNo "Continue with disabling hibernation?" $true) { Disable-Hibernation }
    if (Read-YesNo "Continue with DISM component cleanup? This can take time." $true) { Invoke-DismCleanup }
    Export-Reports
    Write-Log "Full strike sequence completed"
}

Ensure-Admin
$script:Actions = @()
$script:TopItems = @()
"" | Out-File -FilePath $LogFile -Encoding utf8

while ($true) {
    Show-MenuHeader
    Write-Host "Menu:" -ForegroundColor Cyan
    Write-Host "1. Deep analyze drive C"
    Write-Host "2. Safe + aggressive cache cleanup"
    Write-Host "3. Disable hibernation"
    Write-Host "4. DISM component cleanup"
    Write-Host "5. Open virtual memory settings"
    Write-Host "6. Open uninstall center"
    Write-Host "7. Export reports"
    Write-Host "8. Full strike (analyze + clean + hibernation + DISM + export)"
    Write-Host "0. Exit"
    Write-Host ""
    $choice = Read-Host "Select"

    switch ($choice) {
        "1" { Analyze-CDrive; Pause }
        "2" { Invoke-SafeAndAggressiveCleanup; Pause }
        "3" { Disable-Hibernation; Pause }
        "4" { Invoke-DismCleanup; Pause }
        "5" { Open-PagefileSettings; Pause }
        "6" { Open-UninstallCenter; Pause }
        "7" { if (-not $script:TopItems -or $script:TopItems.Count -eq 0) { Analyze-CDrive }; Export-Reports; Pause }
        "8" { Invoke-UltimateStrike; Pause }
        "0" { break }
        default { Write-Host "Invalid input."; Start-Sleep -Seconds 1 }
    }
}
