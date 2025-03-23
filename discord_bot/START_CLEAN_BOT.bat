@echo off
cls
COLOR 0A
echo ================================================
echo    AAROHI BOT - 100%% GUARANTEED CLEAN HELP    
echo ================================================
echo.
echo This will start a completely standalone version 
echo of Aarohi that will DEFINITELY have a clean help
echo command without any "No Category" sections.
echo.
echo This version:
echo - Uses your existing config and token
echo - Loads your existing cogs
echo - But has a completely different help command system
echo   that cannot be overridden by any cogs
echo.
echo Press any key to start the bot...
pause > nul
cls

py -3 standalone_bot.py
pause 