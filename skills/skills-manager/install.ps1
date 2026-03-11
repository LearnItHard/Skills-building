# Skills Manager Installer for Windows
# Run: Invoke-WebRequest -Uri "https://raw.githubusercontent.com/LearnItHard/Skills-building/main/skills/skills-manager/install.ps1" | Invoke-Expression

$ErrorActionPreference = "Stop"

$InstallDir = "$env:LOCALAPPDATA\skills-manager"
$BinDir = "$InstallDir\bin"
$ScriptUrl = "https://raw.githubusercontent.com/LearnItHard/Skills-building/main/skills/skills-manager/skills.py"

Write-Host "Installing Skills Manager..." -ForegroundColor Green

# Create directories
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Download the script
Write-Host "Downloading skills.py..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $ScriptUrl -OutFile "$BinDir\skills.py"

# Create wrapper batch file
$WrapperContent = @"
@echo off
python "$BinDir\skills.py" %*
"@
Set-Content -Path "$BinDir\skills.bat" -Value $WrapperContent

# Add to PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$BinDir", "User")
    Write-Host "Added to PATH. Please restart your terminal." -ForegroundColor Yellow
}

Write-Host "✓ Skills Manager installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  skills install LearnItHard/Skills-building/mineru-converter"
Write-Host "  skills list"
Write-Host "  skills uninstall mineru-converter"
