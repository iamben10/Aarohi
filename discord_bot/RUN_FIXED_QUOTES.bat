@echo off
cls
COLOR 0A

echo =================================================
echo       Aarohi Bot - Single Response Quotes
echo =================================================
echo.
echo This version of the bot includes a fixed !quote command
echo that consolidates its response into a single message.
echo.
echo Features:
echo  - Quote command sends only ONE message per execution
echo  - Includes category selection (motivation, success, focus)
echo  - Shows all available categories when none is specified
echo  - Displays quotes in a clean, attractive embed
echo.
echo Just type !quote or !quote [category] in Discord.
echo.
echo Press any key to start the bot...
pause > nul
py -3 standalone_bot.py 