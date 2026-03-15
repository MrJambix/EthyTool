@echo off
REM EthyTool Pipe Diagnostic — Check what's blocking the connection
REM Run as Admin for full diagnostics. Save output and share if stuck.

setlocal enabledelayedexpansion
echo.
echo ============================================================
echo   EthyTool Pipe Diagnostic
echo ============================================================
echo.

REM --- 1. Admin check ---
echo [1] Admin rights
net session >nul 2>&1
if %errorlevel% equ 0 (
    echo     OK - Running as Administrator
) else (
    echo     WARN - NOT running as Administrator
    echo     ^> Injection requires admin. Right-click EthyTool.exe - Run as admin
)
echo.

REM --- 2. Game process ---
echo [2] Ethyrial game process
powershell -NoProfile -Command "$p = Get-Process -Name '*ethyrial*' -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Write-Host '    Found: PID' $_.Id '-' $_.ProcessName } } else { Write-Host '    NOT FOUND - Game is not running' }"
echo.

REM --- 3. Named pipes (EthyToolPipe_*) ---
echo [3] EthyTool named pipes
powershell -NoProfile -Command "$pipes = Get-ChildItem '\\.\pipe\' -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'EthyTool*' }; if ($pipes) { $pipes | ForEach-Object { Write-Host '    Found:' $_.Name } } else { Write-Host '    NONE - Pipe not created (DLL not injected or crashed)' }"
echo.

REM --- 4. DLL loaded in game? ---
echo [4] EthyTool.dll loaded in game process
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check_pipe_block.ps1" -Section 4
echo.

REM --- 5. EthyTool files ---
echo [5] EthyTool files
set "SCRIPT_DIR=%~dp0"
set "EXE=%SCRIPT_DIR%EthyTool.exe"
set "DLL=%SCRIPT_DIR%EthyTool.dll"
set "DLL_ALT=%~dp0..\EthyTool.dll"
if exist "%EXE%" (echo     EthyTool.exe: OK) else (echo     EthyTool.exe: MISSING)
if exist "%DLL%" (echo     EthyTool.dll: OK) else (if exist "%DLL_ALT%" (echo     EthyTool.dll: OK ^(parent folder^)) else (echo     EthyTool.dll: MISSING or bundled in exe))
echo.

REM --- 6. Windows Defender exclusions (optional) ---
echo [6] Windows Defender - EthyTool folder excluded?
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check_pipe_block.ps1" -Section 6
echo.

REM --- 7. Quick connect test ---
echo [7] Quick pipe connect test
powershell -NoProfile -Command "$procs = Get-Process -Name '*ethyrial*' -ErrorAction SilentlyContinue; if ($procs) { $gpid = $procs[0].Id; try { $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', \"EthyToolPipe_$gpid\", [System.IO.Pipes.PipeDirection]::InOut); $pipe.Connect(2000); $pipe.Close(); Write-Host '    SUCCESS - Pipe connected!' } catch { Write-Host '    FAILED -' $_.Exception.Message } } else { Write-Host '    (no game process)' }"
echo.

echo ============================================================
echo   Summary
echo ============================================================
echo   If pipe not found: 1) Game running ^  2) Inject DLL ^  3) Run as admin
echo   If still stuck: Reboot, add exclude, restart game
echo.
echo   To save output: check_pipe_block.bat ^> pipe_check.txt
echo ============================================================
echo.
pause
