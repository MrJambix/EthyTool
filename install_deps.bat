@echo off
title EthyTool — Runtime Prerequisites
echo.
echo  ============================================
echo   EthyTool Runtime Prerequisites Installer
echo  ============================================
echo.
echo  EthyTool.exe is fully self-contained.
echo  No Python install required.
echo.
echo  This will install the only external runtime
echo  dependency: Microsoft Visual C++ Redistributable
echo  (required by the bundled OpenCV / numpy DLLs).
echo.
echo  If you already ran EthyTool.exe successfully,
echo  you can close this window — you're already good.
echo.
pause

:: ── Check if VC++ 2015-2022 x64 is already installed ──────────────
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  Visual C++ Redistributable is already installed.
    goto :done
)

echo.
echo  Downloading Microsoft Visual C++ Redistributable (x64)...
echo  Source: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.

powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP%\vc_redist.x64.exe'"

if errorlevel 1 (
    echo.
    echo  [ERROR] Download failed. Check your internet connection.
    echo  You can manually download from:
    echo  https://aka.ms/vs/17/release/vc_redist.x64.exe
    pause
    exit /b 1
)

echo  Installing (you may see a UAC prompt)...
"%TEMP%\vc_redist.x64.exe" /install /quiet /norestart

if errorlevel 1 (
    echo.
    echo  [ERROR] Installation failed. Try running as Administrator.
    pause
    exit /b 1
)

:done
echo.
echo  ============================================
echo   Ready! Double-click EthyTool.exe to launch.
echo  ============================================
echo.
pause
