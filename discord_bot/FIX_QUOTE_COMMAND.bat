@echo off
cls
COLOR 0A

echo ================================================
echo    AAROHI BOT - FIXING QUOTE COMMAND DIRECTLY
echo ================================================
echo.
echo This will modify your original productivity.py file 
echo to fix the !quote command so it only sends ONE message.
echo.
echo A backup will be created before any changes are made.
echo.
echo After this runs, you can start your bot NORMALLY
echo with your regular START_GUIDE_BOT.bat file!
echo.
echo Press any key to apply the fix...
pause > nul

py -3 direct_quote_fix.py

echo.
echo Press any key to exit...
pause > nul 