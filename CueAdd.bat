@echo off

:: Bypass authentication
echo Bypassing authentication...

:: Show debug output
set DEBUG_MODE=TRUE
if %DEBUG_MODE%==TRUE (
    echo Debug mode activated.
)

:: Launch main program with error handling
start /wait MyMainProgram.exe
if ERRORLEVEL 1 (
    echo An error occurred while launching the main program.
    exit /b 1
)
echo Program launched successfully!