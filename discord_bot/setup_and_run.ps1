# PowerShell script to download Python, install it, and run the bot
Write-Host "Setting up Python and running your Discord bot..." -ForegroundColor Green

# Create temporary directory for downloads
$tempDir = "$env:TEMP\PythonSetup"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$pythonInstallerPath = "$tempDir\python_installer.exe"

# Download Python installer
Write-Host "Downloading Python installer..." -ForegroundColor Yellow
$url = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile $pythonInstallerPath

# Install Python with PATH option enabled
Write-Host "Installing Python (this may take a minute)..." -ForegroundColor Yellow
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait

# Refresh environment variables to get the new PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Change to the Discord bot directory
Set-Location -Path "$env:USERPROFILE\discord_bot"

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "pip", "install", "-r", "requirements.txt" -Wait

# Run the bot
Write-Host "Starting the Discord bot..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "main.py" -NoNewWindow -Wait

Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 