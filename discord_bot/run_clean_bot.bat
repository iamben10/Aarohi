@echo off
echo ====================================================
echo Running Aarohi with COMPLETELY REDESIGNED HELP COMMAND
echo ====================================================
echo.
echo This version uses a completely new approach:
echo 1. The help command is intercepted BEFORE any other processing
echo 2. NO default help command or cog-based help commands are used
echo 3. ONLY the clean Aarohi Commands section will be displayed
echo.
echo Stopping any existing bot processes...
taskkill /F /FI "WINDOWTITLE eq Aarohi*" /T > nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *Discord Bot*" /T > nul 2>&1
timeout /t 2 /nobreak > nul
echo.
echo Starting Aarohi with clean help command...
py -3 clean_main.py
pause 