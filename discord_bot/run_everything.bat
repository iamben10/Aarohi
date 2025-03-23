@echo off
echo Starting Discord Bot Setup...
echo This will download and install Python automatically

:: Run the PowerShell script with Admin privileges
powershell -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1"

echo If the script didn't run, please right-click this batch file and "Run as administrator"
pause 