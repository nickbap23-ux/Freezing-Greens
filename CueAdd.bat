@echo off
title CueAdd - Elite Edition
color 0A

REM Change to the runtime directory where all files are
cd /d "%~dp0runtime"

REM Run with admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo [!] Administrator privileges required
    echo Please right-click and "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo Launching authentication...
echo.

REM Step 1: Run authentication with Python 3.11
REM Internal module names (compiled - do not rename)
py -3.11 -c "import FreezingGreens_Secure" 2>nul
if %errorLevel% neq 0 (
    py -3.11 "FreezingGreens_Secure.pyc" 2>nul
    if %errorLevel% neq 0 (
        echo.
        echo [X] Authentication failed
        pause
        exit /b 1
    )
)

echo.
echo Launching CueAdd...
echo.

REM Step 2: Run CueAdd main program
py -3.11 -c "import freezinggreens; freezinggreens.main()"

echo.
echo CueAdd closed
pause
