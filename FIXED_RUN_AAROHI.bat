@echo off
title Aarohi Bot - Fixed Version
color 0A

echo ===============================================
echo            AAROHI BOT LAUNCHER
echo            (FIXED VERSION)
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

:: Check if config.json exists and contains a token
set CONFIG_OK=0
if exist config.json (
    python -c "import json; f=open('config.json'); d=json.load(f); print('TOKEN_OK' if 'token' in d and len(d['token'])>10 else 'TOKEN_MISSING')" > token_check.tmp
    set /p TOKEN_STATUS=<token_check.tmp
    del token_check.tmp
    
    if "%TOKEN_STATUS%"=="TOKEN_OK" (
        set CONFIG_OK=1
        echo Config file validated successfully.
    ) else (
        echo Config file exists but token appears invalid.
        set CONFIG_OK=0
    )
) else (
    echo Config file not found.
    set CONFIG_OK=0
)

if %CONFIG_OK%==0 (
    echo Creating new config file...
    echo Please enter your Discord bot token:
    set /p BOT_TOKEN=
    echo {"token": "%BOT_TOKEN%", "prefix": "!"} > config.json
    echo Config file created successfully.
)

echo.
echo ===============================================
echo       STARTING AAROHI WITH CHANNEL RESTRICTION
echo ===============================================
echo.
echo [INFO] Channel restriction: Bot will only respond in channel ID 1353429400460198032
echo [INFO] Bot is starting up, please wait...
echo.

:: Run the bot
python standalone_bot.py

echo.
if %ERRORLEVEL% neq 0 (
    echo Error occurred while running the bot. Check the logs for details.
) else (
    echo Bot has shut down gracefully.
)

echo Press any key to exit...
pause > nul 