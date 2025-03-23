@echo off
echo Creating desktop shortcut for Aarohi Bot Restarter...
echo.

:: Get the full path to the restart_bot.bat file
set "SCRIPT_PATH=%~dp0restart_bot.bat"
echo Script path: %SCRIPT_PATH%

:: Try multiple methods to find the Desktop path
echo Detecting Desktop location...

:: Method 1: Standard user profile desktop
set "DESKTOP_PATH=%USERPROFILE%\Desktop"
if not exist "%DESKTOP_PATH%" (
    :: Method 2: OneDrive desktop
    set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Desktop"
    if not exist "%DESKTOP_PATH%" (
        :: Method 3: Use shell folders registry
        for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Desktop" 2^>nul') do set "DESKTOP_PATH=%%b"
        if not exist "%DESKTOP_PATH%" (
            echo Could not find Desktop folder automatically.
            echo.
            echo Please enter your Desktop path manually (e.g. C:\Users\YourName\Desktop):
            set /p DESKTOP_PATH=
        )
    )
)

echo Desktop path: %DESKTOP_PATH%
echo.

:: Check if the desktop path exists
if not exist "%DESKTOP_PATH%" (
    echo ERROR: The desktop path does not exist.
    echo Creating the shortcut directly in the current folder instead.
    set "DESKTOP_PATH=%~dp0"
)

:: Create the shortcut using PowerShell
echo Creating shortcut...
powershell -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_PATH%\Restart Aarohi Bot.lnk'); $Shortcut.TargetPath = '%SCRIPT_PATH%'; $Shortcut.IconLocation = 'shell32.dll,175'; $Shortcut.Description = 'Restart Aarohi Discord Bot'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"

:: Check if successful
set "SHORTCUT_PATH=%DESKTOP_PATH%\Restart Aarohi Bot.lnk"
if exist "%SHORTCUT_PATH%" (
    echo.
    echo Success! Shortcut created at:
    echo %SHORTCUT_PATH%
) else (
    echo.
    echo Failed to create shortcut at:
    echo %SHORTCUT_PATH%
    echo.
    echo Trying alternative method...
    
    :: Try alternative with VBScript
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\createshortcut.vbs"
    echo sLinkFile = "%DESKTOP_PATH%\Restart Aarohi Bot.lnk" >> "%TEMP%\createshortcut.vbs"
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\createshortcut.vbs"
    echo oLink.TargetPath = "%SCRIPT_PATH%" >> "%TEMP%\createshortcut.vbs"
    echo oLink.WorkingDirectory = "%~dp0" >> "%TEMP%\createshortcut.vbs"
    echo oLink.Description = "Restart Aarohi Discord Bot" >> "%TEMP%\createshortcut.vbs"
    echo oLink.IconLocation = "shell32.dll,175" >> "%TEMP%\createshortcut.vbs"
    echo oLink.Save >> "%TEMP%\createshortcut.vbs"
    cscript //nologo "%TEMP%\createshortcut.vbs"
    del "%TEMP%\createshortcut.vbs"
    
    if exist "%SHORTCUT_PATH%" (
        echo.
        echo Success with alternative method! Shortcut created at:
        echo %SHORTCUT_PATH%
    ) else (
        echo.
        echo Both methods failed. Creating a copy of the restart script directly.
        echo.
        copy "%SCRIPT_PATH%" "%DESKTOP_PATH%\Restart Aarohi Bot.bat" > nul
        if exist "%DESKTOP_PATH%\Restart Aarohi Bot.bat" (
            echo Created a copy of the restart script at:
            echo %DESKTOP_PATH%\Restart Aarohi Bot.bat
        ) else (
            echo All methods failed. You can still use restart_bot.bat directly from:
            echo %SCRIPT_PATH%
        )
    )
)

echo.
echo Would you like to create a Start Menu shortcut instead? (Y/N)
choice /c YN /n
if %ERRORLEVEL% EQU 1 (
    :: Create Start Menu shortcut
    set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
    powershell -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\Restart Aarohi Bot.lnk'); $Shortcut.TargetPath = '%SCRIPT_PATH%'; $Shortcut.IconLocation = 'shell32.dll,175'; $Shortcut.Description = 'Restart Aarohi Discord Bot'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
    echo.
    echo Start Menu shortcut created at:
    echo %START_MENU%\Restart Aarohi Bot.lnk
)

echo.
echo Would you like to pin the restart bat to your taskbar? (Y/N)
choice /c YN /n
if %ERRORLEVEL% EQU 1 (
    echo This will open the file location. Right-click the file and select "Pin to taskbar".
    explorer /select,"%SCRIPT_PATH%"
)

echo.
echo Press any key to exit...
pause > nul 