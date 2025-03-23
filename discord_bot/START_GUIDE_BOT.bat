@echo off
cls
COLOR 0A
echo ================================================
echo         AAROHI BOT - GUIDE COMMAND           
echo ================================================
echo.
echo This version of Aarohi uses !guide instead of !help
echo to show the clean commands list without conflicts.
echo.
echo Benefits:
echo - Keeps the original !help command intact
echo - Adds a new !guide command that shows only Aarohi Commands
echo - No conflicts with any existing code
echo - All other commands and features work normally
echo.
echo Usage:
echo - Type !guide to see the clean commands list
echo - Type !help for the regular help (with categories)
echo.
echo Press any key to start the bot...
pause > nul
cls

py -3 standalone_bot.py
pause 