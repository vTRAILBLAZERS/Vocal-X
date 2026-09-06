@echo off
setlocal
title Vocal X Developer Setup
cd /d "%~dp0"
echo.
echo ============================================================
echo  VOCAL X - DEVELOPER SETUP
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tools\Setup-VocalX-Developer.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
    echo ============================================================
    echo  SETUP FAILED - EXIT CODE %EXITCODE%
    echo ============================================================
    echo.
    pause
    exit /b %EXITCODE%
)
echo ============================================================
echo  VOCAL X SETUP COMPLETED
echo ============================================================
echo.
pause
exit /b 0
