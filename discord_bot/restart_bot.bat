@echo off
echo =========================
echo Aarohi Discord Bot Restarter
echo =========================
echo.

:start

:: Kill any existing Python processes running main.py (the bot)
echo Stopping any existing bot processes...
taskkill /F /FI "WINDOWTITLE eq Aarohi Discord Bot" /T > nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *Discord Bot*" /T > nul 2>&1

:: Wait a moment for processes to close
timeout /t 1 /nobreak > nul

:: Clear the screen
cls

:: Set title for the window
title Aarohi Discord Bot

:: Display a nice ASCII art header
echo.
echo    _____            ____  ____  __  __ _____ 
echo   /\    \         /\    V    \/\ \/\ \\_   \
echo  /::\    \       /::\____:____\:\ \:\ \//\__\
echo /::::\    \     /:::://  \//\  \:\ \:\ \/ /  /
echo /::::::\    \   /::://    \::\  \:\_\:\ \/  / 
echo /:::/\:::\    \ /::://      \\:\  \  _\:\  /  
echo /:::/__\:::\    /::://        \\:\ \ \/\:\ \  
echo \:::\   \:::\  /::://___________\\:\_\__\:\ \ 
echo  \:::\   \:::\/::///______________\/_____\:\ \
echo   \:::\   \::::::///________________________\:\ \
echo    \:::\   \::::::/ ________________________/::/ 
echo     \:::\   \::::/                     /:::/    
echo      \:::\  /:::/                     /:::/     
echo       \:::\/:::/                     /:::/      
echo        \::::::/                     /:::/       
echo         \::::/                     /::::/       
echo          ^^^""                       ^^^"""        
echo.
echo =========================
echo Aarohi Discord Bot is Starting...
echo =========================

:: Start the bot in the same window
python main.py

:: This will only run if the bot crashes or exits
echo.
echo Bot has stopped running.
echo Press any key to restart...
pause > nul
cls
echo Restarting...
goto start 