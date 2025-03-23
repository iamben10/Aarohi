@echo off
cls
COLOR 0A

echo ================================================
echo       AAROHI BOT - COMPLETE COMMAND OVERHAUL
echo ================================================
echo.
echo This version of Aarohi has been COMPLETELY overhauled:
echo.
echo 1. ALL COMMANDS WORK INDEPENDENTLY - no more required !guide
echo 2. CLEAN HELP MENU - exactly as specified, with no extra junk
echo 3. SINGLE RESPONSES - every command sends only one message
echo 4. ALL COMMANDS IMPLEMENTED - including pomodoro, todo, alarm,
echo    focus, profile, mood, resources and quote commands
echo.
echo Commands use !help instead of !guide now.
echo.
echo Press any key to start Aarohi...
pause > nul
py -3 standalone_bot.py 