@echo off
REM EthyTool — Full Install (Dependencies + Defender + Firewall)
REM Run as Admin for full setup. Right-click -> Run as administrator.

setlocal enabledelayedexpansion
title EthyTool — Full Install

:: ── Self-elevate to Admin if not already ─────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b 0
)

echo.
echo ============================================================
echo   EthyTool — Full Install (Run Out of the Box)
echo ============================================================
echo.
echo  This will:
echo    1. Install Visual C++ Redistributable (required by OpenCV/numpy)
echo    2. Add Windows Defender exclusion for this folder
echo    3. Add Firewall rules for EthyTool.exe
echo    4. Install Python packages (optional, for build/run-from-source)
echo.
echo  Run as Administrator for all steps.
echo.
pause

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "EXE=%SCRIPT_DIR%\EthyTool.exe"

:: ── 1. Visual C++ Redistributable ──────────────────────────────
echo.
echo [1/4] Visual C++ Redistributable (x64)
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>&1
if not errorlevel 1 (
    echo     Already installed.
) else (
    echo     Downloading...
    powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP%\vc_redist.x64.exe' -UseBasicParsing }"
    if errorlevel 1 (
        echo     [ERROR] Download failed. Check internet. Manual: https://aka.ms/vs/17/release/vc_redist.x64.exe
    ) else (
        echo     Installing...
        "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
        if errorlevel 1 (echo     [WARN] Install failed - try manual install) else (echo     Installed.)
    )
)

:: ── 2. Windows Defender exclusion ───────────────────────────────
echo.
echo [2/4] Windows Defender exclusion
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $path = '%SCRIPT_DIR%'; $p = Get-MpPreference -ErrorAction SilentlyContinue; if ($p) { $existing = $p.ExclusionPath | Where-Object { $_ -like '*EthyTool*' -or $_ -eq $path }; if ($existing) { Write-Host '    Already excluded.' } else { Add-MpPreference -ExclusionPath $path; Write-Host '    Added exclusion for:' $path } } else { Write-Host '    Defender not active or inaccessible.' } }"
if errorlevel 1 (
    echo     [WARN] Could not add exclusion. Add manually in Windows Security.
)

:: ── 3. Firewall rules ───────────────────────────────────────────
echo.
echo [3/4] Firewall rules
:: Use temp file to pass path (avoids "unexpected at this time" when path has parentheses)
set "EXE_PATH_FILE=%TEMP%\ethytool_exe_path.txt"
echo !EXE!> "!EXE_PATH_FILE!"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_firewall.ps1" -PathFile "!EXE_PATH_FILE!"
if errorlevel 1 (
    echo     [WARN] Firewall rules failed or EthyTool.exe not found.
)
del "!EXE_PATH_FILE!" 2>nul

:: ── 4. Python dependencies (optional, for build) ──────────────────
echo.
echo [4/4] Python dependencies (optional)
set "REQ=!SCRIPT_DIR!\requirements.txt"
if exist "!REQ!" (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        echo     Installing packages from requirements.txt...
        python -m pip install -r "!REQ!" --upgrade
        if !errorlevel! equ 0 (echo     Done.) else (echo     [WARN] pip had errors.)
    ) else (
        echo     Python not found - skipping. EthyTool.exe is self-contained.
    )
) else (
    echo     requirements.txt not found - skipping.
)

:: ── Summary ──────────────────────────────────────────────────────
echo.
echo ============================================================
echo   Done
echo ============================================================
echo.
echo  Next steps:
echo    1. Launch Ethyrial (game)
echo    2. Run EthyTool.exe as Administrator
echo    3. Inject EthyTool.dll into the game
echo    4. Click Connect
echo.
echo  If pipe issues: run check_pipe_block.bat
echo ============================================================
echo.
pause
