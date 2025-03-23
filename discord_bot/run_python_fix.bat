@echo off
echo Attempting to run the Discord bot...

REM Try Microsoft Store Python
echo Trying Microsoft Store Python...
C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe main.py
if %ERRORLEVEL% == 0 goto :end

REM Try common Python installation locations
echo Trying common Python installation paths...
IF EXIST "C:\Python311\python.exe" (
    "C:\Python311\python.exe" main.py
    goto :end
)

IF EXIST "C:\Python310\python.exe" (
    "C:\Python310\python.exe" main.py
    goto :end
)

IF EXIST "C:\Python39\python.exe" (
    "C:\Python39\python.exe" main.py
    goto :end
)

IF EXIST "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" main.py
    goto :end
)

IF EXIST "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe" main.py
    goto :end
)

IF EXIST "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" main.py
    goto :end
)

echo ERROR: Could not find Python in any common location.
echo Please install Python from https://www.python.org/downloads/
echo Be sure to check "Add Python to PATH" during installation.
pause

:end
pause 