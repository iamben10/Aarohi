@echo off
title Aarohi Bot
color 0A

echo ===============================================
echo            AAROHI BOT LAUNCHER
echo ===============================================
echo.
echo Initializing Aarohi Bot...
echo.

:: Change to the bot directory
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

echo Installing/updating required packages...
python -m pip install -U discord.py flask pytz pickle-mixin --quiet

:: Check if PyNaCl is installed (for voice support)
python -c "import nacl" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing PyNaCl for voice support...
    python -m pip install PyNaCl --quiet
)

:: Check if config.json exists
if not exist config.json (
    echo Config file not found. Creating one...
    echo Please enter your bot token:
    set /p TOKEN=
    echo {"token": "%TOKEN%", "prefix": "!"} > config.json
    echo Config file created.
)

echo.
echo ===============================================
echo       STARTING AAROHI WITH FIXED PIPELINE
echo ===============================================
echo.
echo [INFO] Using optimized heartbeat configuration
echo [INFO] Bot is starting up, please wait...
echo.

:: Run the bot with improved settings
python standalone_bot.py

echo.
echo Bot has stopped. Check logs for any errors.
echo Press any key to exit...
pause > nul
