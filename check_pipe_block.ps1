# EthyTool Pipe Diagnostic - PowerShell (called by check_pipe_block.bat)
# Avoids batch quoting issues for [4] and [6]

param([string]$Section)

if ($Section -eq "4") {
    $procs = Get-Process -Name '*ethyrial*' -ErrorAction SilentlyContinue
    foreach ($proc in $procs) {
        try {
            $mods = $proc.Modules | Where-Object { $_.ModuleName -like '*EthyTool*' }
        } catch {
            $mods = $null
        }
        if ($mods) {
            Write-Host "    OK - EthyTool.dll loaded in PID $($proc.Id)"
        } else {
            Write-Host "    NOT LOADED in PID $($proc.Id) - Inject the DLL first"
        }
    }
    if (-not $procs) { Write-Host "    (no game process to check)" }
}
elseif ($Section -eq "6") {
    try {
        $prefs = Get-MpPreference -ErrorAction Stop
        $found = $prefs.ExclusionPath | Where-Object { $_ -like '*EthyTool*' }
        if ($found) {
            Write-Host "    Excluded:" ($found -join ', ')
        } else {
            Write-Host "    Not excluded - Add EthyTool folder if AV blocks"
        }
    } catch {
        Write-Host "    (Could not read - run as admin or Defender not active)"
    }
}
