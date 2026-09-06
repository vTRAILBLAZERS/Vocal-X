@echo off
setlocal
title Vocal X Developer
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "APP=%~dp0App\vocal_gui.py"

if not exist "%PYTHON%" (
    echo.
    echo [ERROR] Vocal X Python environment was not found.
    echo Run "Setup Vocal X Developer.cmd" first.
    echo.
    pause
    exit /b 10
)

if not exist "%APP%" (
    echo.
    echo [ERROR] Vocal X GUI entrypoint was not found.
    echo %APP%
    echo.
    pause
    exit /b 11
)

"%PYTHON%" "%APP%"
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo Vocal X exited with code %EXITCODE%.
    echo.
    pause
)

exit /b %EXITCODE%
