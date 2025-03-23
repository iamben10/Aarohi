@echo off
cls
COLOR 0A

echo ================================================
echo   AAROHI BOT - FULLY RELIABLE ALARM SYSTEM
echo ================================================
echo.
echo Installing required packages first...
py -3 -m pip install pytz

echo.
echo ================================================
echo.
echo This version of Aarohi includes:
echo.
echo 1. BULLETPROOF ALARM SYSTEM - Alarms WILL ring exactly on time
echo 2. 100%% RELIABLE - Using asyncio-based scheduling system
echo 3. PERSISTENT ALARMS - Alarms are saved even if bot restarts
echo 4. TIME ZONE HANDLING - Consistent timing regardless of server
echo 5. ENHANCED FEATURES - Add messages to alarms and clear all alarms
echo.
echo Commands:
echo   !alarm HH:MM [message] - Set an alarm for specific time
echo   !alarm                 - View your current alarms
echo   !alarm clear           - Remove all your alarms
echo.
echo Press any key to start Aarohi with reliable alarms...
pause > nul
py -3 standalone_bot.py 