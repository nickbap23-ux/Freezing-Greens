@echo off
title CueAdd - Dependency Installer
color 0A

echo.
echo  ============================================
echo   CueAdd - Dependency Installer
echo  ============================================
echo.

:: Check for Python 3.11
echo [*] Checking for Python 3.11...
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python 3.11 is NOT installed!
    echo.
    echo  Please download and install Python 3.11 from:
    echo  https://www.python.org/downloads/release/python-3119/
    echo.
    echo  IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    pause
    start https://www.python.org/downloads/release/python-3119/
    exit /b 1
)

echo [+] Python 3.11 found!
echo.

:: Install required packages
echo [*] Installing required packages...
echo.

py -3.11 -m pip install --upgrade pip >nul 2>&1

echo     Installing PyQt6...
py -3.11 -m pip install PyQt6
if %errorlevel% neq 0 (
    echo     [!] PyQt6 install failed, trying with --user flag...
    py -3.11 -m pip install --user PyQt6
)

echo     Installing requests...
py -3.11 -m pip install requests

echo     Installing numpy...
py -3.11 -m pip install numpy

echo     Installing psutil...
py -3.11 -m pip install psutil

echo.
echo  ============================================
echo   Installation Complete!
echo  ============================================
echo.
echo  You can now run CueAdd.bat
echo.
pause
