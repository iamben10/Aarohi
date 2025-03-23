@echo off
echo =========================
echo Aarohi Help Command Fix
echo =========================
echo.
echo This script will restart Aarohi with the fixed help command.
echo The help command has been completely rewritten to eliminate duplicates.
echo.
echo COMPREHENSIVE FIX APPROACH:
echo 1. Set help_command=None when initializing the bot
echo 2. Created a simple @bot.command(name="help") for the clean help output
echo 3. Added special handling in main.py on_message to intercept help commands
echo 4. Added early return checks in all cog on_message handlers for help command
echo.
echo Press any key to restart the bot...
pause > nul

:: Stop any existing bot process
echo Stopping any existing bot processes...
taskkill /F /FI "WINDOWTITLE eq Aarohi*" /T > nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *Discord Bot*" /T > nul 2>&1

timeout /t 2 /nobreak > nul

:: Clear the screen
cls

:: Start the bot with error handling
echo Starting Aarohi with fixed help command...
echo.
echo If you encounter any errors:
echo 1. Make sure all file edits have been saved
echo 2. Check for any syntax errors in the Python files
echo 3. The main fixes are in three places:
echo    - main.py: Updated bot initialization and added special help intercept
echo    - conversation.py: Added early return for help commands
echo    - introduction_handler.py: Added early return for help commands
echo.

:: Start the bot in a new window with a good title
start "Aarohi Discord Bot - Fixed Help Command" cmd /k "python main.py"

echo.
echo Aarohi has been restarted!
echo.
echo To test the fix:
echo - Type !help in any channel
echo - Verify that ONLY the clean help message appears exactly as requested
echo - There should be NO duplicate sections or ANY additional text
echo.
echo The final solution implements a multi-layered approach:
echo 1. Disables the default help command system completely (help_command=None)
echo 2. Creates a direct @bot.command handler for "help" with the exact format you specified
echo 3. Adds special interception of help commands in ALL on_message handlers
echo 4. Adds direct interception in main.py before any cog processing occurs
echo.
echo This ensures that ONLY one handler processes the help command, with NO duplicates.
echo.
echo Press any key to exit...
pause > nul

@echo off
echo Fixing the help command in main.py...

:: Create a backup of the original file
copy main.py main.py.backup
echo Created backup as main.py.backup

:: Replace the help command with the optimized version
powershell -Command "$content = Get-Content -path 'new_help_command.py' -Raw; $mainContent = Get-Content -path 'main.py' -Raw; $pattern = '# Simple help command using the standard decorator[\s\S]*?@bot\.command\(name=\"help\"\)[\s\S]*?async def help\(ctx, command: str = None\):[\s\S]*?"""[\s\S]*?"""[\s\S]*?if command is None:[\s\S]*?embed = discord\.Embed\([\s\S]*?await ctx\.send\(embed=embed\)[\s\S]*?return'; $replacement = $content; $result = $mainContent -replace $pattern, $content; Set-Content -path 'main.py' -Value $result;"

echo Done! The help command has been updated.
echo Run the bot to see the changes in action!
echo.
echo Press any key to exit...
pause > nul 